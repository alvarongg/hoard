"""Business logic for database backups: create, verify, restore, retention."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.app_setting import AppSetting
from api.schemas.backup import (
    BackupConfig,
    BackupConfigUpdate,
    BackupInfo,
    RestoreResult,
)
from core.exceptions import NotFoundError, ToolUnavailableError, ValidationError

SCHEMA_VERSION = "1.0"
CONFIG_KEY = "backups.config"


class BackupService:
    """Creates and manages database backup archives."""

    def __init__(self, db: AsyncSession, backup_dir: str, database_url: str) -> None:
        self._db = db
        self._dir = Path(backup_dir)
        self._database_url = database_url

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(self, trigger: str = "manual") -> BackupInfo:
        """Create a backup archive.

        Raises:
            ToolUnavailableError: If pg_dump is not on PATH.
        """
        if shutil.which("pg_dump") is None:
            raise ToolUnavailableError(
                "pg_dump is not available; install the PostgreSQL client"
            )

        self._dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        short = uuid4().hex[:8]
        name = f"hoard-backup-{ts}-{short}.tar.gz"
        archive_path = self._dir / name

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dump_path = tmp_path / "database.dump"
            subprocess.run(
                ["pg_dump", "-Fc", "-f", str(dump_path), self._database_url],
                check=True,
                capture_output=True,
            )
            checksum = self._sha256(dump_path)
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "created_at": datetime.now(UTC).isoformat(),
                "trigger": trigger,
                "database_sha256": checksum,
            }
            (tmp_path / "manifest.json").write_text(json.dumps(manifest))
            # config.json with non-sensitive settings only (never SECRET_KEY/DATABASE_URL)
            (tmp_path / "config.json").write_text(
                json.dumps({"schema_version": SCHEMA_VERSION})
            )
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(dump_path, arcname="database.dump")
                tar.add(tmp_path / "manifest.json", arcname="manifest.json")
                tar.add(tmp_path / "config.json", arcname="config.json")

        stat = archive_path.stat()
        return BackupInfo(
            id=name,
            filename=name,
            created_at=datetime.now(UTC),
            size_bytes=stat.st_size,
            trigger=trigger,
        )

    # ------------------------------------------------------------------
    # List / get / delete / retention
    # ------------------------------------------------------------------

    def list(self) -> list[BackupInfo]:
        if not self._dir.exists():
            return []
        infos: list[BackupInfo] = []
        for p in self._dir.glob("hoard-backup-*.tar.gz"):
            stat = p.stat()
            infos.append(
                BackupInfo(
                    id=p.name,
                    filename=p.name,
                    created_at=datetime.fromtimestamp(stat.st_mtime, UTC),
                    size_bytes=stat.st_size,
                    trigger="unknown",
                )
            )
        infos.sort(key=lambda i: i.created_at, reverse=True)
        return infos

    def get_path(self, backup_id: str) -> Path:
        path = self._dir / backup_id
        if not self._is_safe_child(path) or not path.exists():
            raise NotFoundError(f"Backup '{backup_id}' not found")
        return path

    def delete(self, backup_id: str) -> None:
        path = self.get_path(backup_id)
        path.unlink()

    def apply_retention(self, retention_count: int) -> int:
        """Keep exactly min(retention_count, existing) newest backups.

        Returns the number of backups deleted.
        """
        backups = self.list()
        to_delete = backups[retention_count:]
        for b in to_delete:
            (self._dir / b.filename).unlink(missing_ok=True)
        return len(to_delete)

    # ------------------------------------------------------------------
    # Verify + restore
    # ------------------------------------------------------------------

    def _verify(self, path: Path) -> tuple[bool, str | None]:
        # 1. tar readable
        try:
            with tarfile.open(path, "r:gz") as tar:
                members = tar.getmembers()
                names = {m.name for m in members}
                # path-traversal guard
                for m in members:
                    if m.name.startswith("/") or ".." in Path(m.name).parts:
                        return False, "unsafe member path in archive"
                if "manifest.json" not in names or "database.dump" not in names:
                    return False, "archive missing required members"
                manifest_raw = tar.extractfile("manifest.json")
                dump_member = tar.extractfile("database.dump")
                if manifest_raw is None or dump_member is None:
                    return False, "cannot read archive members"
                # 2. manifest valid + supported version
                try:
                    manifest = json.loads(manifest_raw.read().decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return False, "invalid manifest.json"
                if manifest.get("schema_version") != SCHEMA_VERSION:
                    return False, "unsupported backup schema_version"
                # 3. checksum
                digest = hashlib.sha256(dump_member.read()).hexdigest()
                if digest != manifest.get("database_sha256"):
                    return False, "checksum mismatch"
        except tarfile.TarError:
            return False, "archive is not a readable tar.gz"
        return True, None

    def restore(self, backup_id: str) -> RestoreResult:
        """Restore from a backup, only if verification passes.

        Raises:
            NotFoundError: If the backup does not exist.
            ValidationError: If the archive fails verification.
            ToolUnavailableError: If pg_restore is not on PATH.
        """
        path = self.get_path(backup_id)
        valid, reason = self._verify(path)
        if not valid:
            raise ValidationError(f"Backup verification failed: {reason}")
        if shutil.which("pg_restore") is None:
            raise ToolUnavailableError(
                "pg_restore is not available; install the PostgreSQL client"
            )
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(path, "r:gz") as tar:
                tar.extract("database.dump", tmp)  # noqa: S202 (verified above)
            dump = os.path.join(tmp, "database.dump")
            subprocess.run(
                ["pg_restore", "--clean", "--if-exists", "-d",
                 self._database_url, dump],
                check=True,
                capture_output=True,
            )
        return RestoreResult(restored=True, filename=backup_id)

    # ------------------------------------------------------------------
    # Config (persisted in app_settings)
    # ------------------------------------------------------------------

    async def get_config(self) -> BackupConfig:
        setting = await self._db.get(AppSetting, CONFIG_KEY)
        if setting is None or not isinstance(setting.value, dict):
            return BackupConfig()
        return BackupConfig(**setting.value)

    async def update_config(self, data: BackupConfigUpdate) -> BackupConfig:
        current = await self.get_config()
        merged = current.model_dump()
        for k, v in data.model_dump(exclude_unset=True).items():
            if v is not None:
                merged[k] = v
        # Validate through the model (retention range enforced by schema).
        validated = BackupConfig(**merged)

        setting = await self._db.get(AppSetting, CONFIG_KEY)
        payload = json.loads(validated.model_dump_json())
        if setting is None:
            self._db.add(AppSetting(key=CONFIG_KEY, value=payload))
        else:
            setting.value = payload
        await self._db.commit()
        return validated

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _is_safe_child(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self._dir.resolve())
            return True
        except ValueError:
            return False
