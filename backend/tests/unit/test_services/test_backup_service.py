"""Unit tests for BackupService (pg_dump mocked)."""

from __future__ import annotations

import hashlib
import json
import tarfile
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from api.schemas.backup import BackupConfigUpdate
from api.services.backup_service import SCHEMA_VERSION, BackupService
from core.exceptions import NotFoundError, ToolUnavailableError, ValidationError


@pytest.fixture()
async def engine():
    from api.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def backup_dir(tmp_path) -> str:
    return str(tmp_path / "backups")


@pytest.fixture
def service(db_session, backup_dir) -> BackupService:
    return BackupService(db_session, backup_dir, "postgresql://x/y")


def _mock_pg_dump(monkeypatch, *, available=True):
    monkeypatch.setattr(
        "api.services.backup_service.shutil.which",
        lambda name: "/usr/bin/pg_dump" if available else None,
    )

    def fake_run(cmd, **kwargs):
        # Write a fake dump file at the -f target.
        if "-f" in cmd:
            target = cmd[cmd.index("-f") + 1]
            Path(target).write_bytes(b"FAKE DUMP CONTENT")

        class R:
            returncode = 0

        return R()

    monkeypatch.setattr(
        "api.services.backup_service.subprocess.run", fake_run
    )


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


async def test_create_produces_archive_with_members(service, monkeypatch):
    _mock_pg_dump(monkeypatch)
    info = await service.create(trigger="manual")
    path = service.get_path(info.id)
    with tarfile.open(path, "r:gz") as tar:
        names = set(tar.getnames())
    assert {"database.dump", "manifest.json", "config.json"} <= names


async def test_create_without_pg_dump_raises(service, monkeypatch):
    _mock_pg_dump(monkeypatch, available=False)
    with pytest.raises(ToolUnavailableError):
        await service.create()


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


def _write_archive(dir_path: Path, *, dump=b"DATA", manifest=None, member_name="database.dump"):
    dir_path.mkdir(parents=True, exist_ok=True)
    name = f"hoard-backup-{uuid4().hex}.tar.gz"
    archive = dir_path / name
    import io

    with tarfile.open(archive, "w:gz") as tar:
        d = io.BytesIO(dump)
        ti = tarfile.TarInfo(member_name)
        ti.size = len(dump)
        tar.addfile(ti, d)
        if manifest is not None:
            m = json.dumps(manifest).encode()
            mi = tarfile.TarInfo("manifest.json")
            mi.size = len(m)
            tar.addfile(mi, io.BytesIO(m))
    return name


async def test_verify_rejects_missing_manifest(service, backup_dir):
    name = _write_archive(Path(backup_dir))  # no manifest
    valid, reason = service._verify(Path(backup_dir) / name)
    assert valid is False


async def test_verify_rejects_bad_version(service, backup_dir):
    dump = b"DATA"
    name = _write_archive(
        Path(backup_dir),
        dump=dump,
        manifest={
            "schema_version": "9.9",
            "database_sha256": hashlib.sha256(dump).hexdigest(),
        },
    )
    valid, reason = service._verify(Path(backup_dir) / name)
    assert valid is False and "version" in (reason or "")


async def test_verify_rejects_checksum_mismatch(service, backup_dir):
    name = _write_archive(
        Path(backup_dir),
        dump=b"DATA",
        manifest={"schema_version": SCHEMA_VERSION, "database_sha256": "wrong"},
    )
    valid, reason = service._verify(Path(backup_dir) / name)
    assert valid is False and "checksum" in (reason or "")


async def test_verify_accepts_valid(service, backup_dir):
    dump = b"DATA"
    name = _write_archive(
        Path(backup_dir),
        dump=dump,
        manifest={
            "schema_version": SCHEMA_VERSION,
            "database_sha256": hashlib.sha256(dump).hexdigest(),
        },
    )
    valid, reason = service._verify(Path(backup_dir) / name)
    assert valid is True and reason is None


async def test_restore_invalid_archive_raises(service, backup_dir):
    name = _write_archive(Path(backup_dir))  # no manifest -> invalid
    with pytest.raises(ValidationError):
        service.restore(name)


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


async def test_config_defaults(service):
    config = await service.get_config()
    assert config.frequency == "weekly"
    assert config.retention_count == 7


async def test_config_update_persists(service):
    updated = await service.update_config(
        BackupConfigUpdate(frequency="daily", retention_count=10)
    )
    assert updated.frequency == "daily"
    reread = await service.get_config()
    assert reread.retention_count == 10


async def test_config_invalid_retention_rejected(service):
    with pytest.raises(Exception):
        BackupConfigUpdate(retention_count=0)


# ---------------------------------------------------------------------------
# retention
# ---------------------------------------------------------------------------


async def test_retention_keeps_min_n_created(service, monkeypatch, backup_dir):
    _mock_pg_dump(monkeypatch)
    for _ in range(5):
        await service.create()
    deleted = service.apply_retention(3)
    assert deleted == 2
    assert len(service.list()) == 3


async def test_get_unknown_raises(service):
    with pytest.raises(NotFoundError):
        service.get_path("hoard-backup-does-not-exist.tar.gz")
