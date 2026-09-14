"""APScheduler-based automatic backup scheduler.

The scheduler runs the backup job on the configured frequency. In a
multi-process deployment a PostgreSQL advisory lock ensures only one
instance runs the job; that lock is a no-op on SQLite (dev/test).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_FREQUENCY_TRIGGERS = {
    "daily": {"days": 1},
    "weekly": {"weeks": 1},
    "monthly": {"days": 30},
}


class BackupScheduler:
    """Owns the AsyncIOScheduler and the backup job lifecycle."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    def schedule(self, frequency: str, job_func) -> None:
        """(Re)schedule the backup job for the given frequency."""
        interval = _FREQUENCY_TRIGGERS.get(frequency, {"weeks": 1})
        self._scheduler.add_job(
            job_func,
            trigger="interval",
            id="hoard-backup",
            replace_existing=True,
            next_run_time=datetime.now(UTC),
            **interval,
        )


async def run_backup_job(session_factory, backup_service_factory) -> str:
    """Execute one scheduled backup with lock + status handling.

    Returns 'ok', 'skipped', or 'failed'. A failure is logged and existing
    backups are preserved (retention is not applied on failure).
    """
    async with session_factory() as session:
        service = backup_service_factory(session)
        # Advisory lock: try to acquire; if another worker holds it, skip.
        acquired = await _try_advisory_lock(session)
        if not acquired:
            return "skipped"
        try:
            await service.create(trigger="scheduled")
            config = await service.get_config()
            service.apply_retention(config.retention_count)
            return "ok"
        except Exception:  # noqa: BLE001
            logger.exception("Scheduled backup failed")
            return "failed"
        finally:
            await _release_advisory_lock(session)


async def _try_advisory_lock(session) -> bool:
    """Acquire the backup advisory lock on PostgreSQL; no-op True on SQLite."""
    from core.dialect import supports_generated_columns

    if not supports_generated_columns(session):
        return True
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT pg_try_advisory_lock(hashtext('hoard.backup'))")
    )
    return bool(result.scalar())


async def _release_advisory_lock(session) -> None:
    from core.dialect import supports_generated_columns

    if not supports_generated_columns(session):
        return
    from sqlalchemy import text

    await session.execute(
        text("SELECT pg_advisory_unlock(hashtext('hoard.backup'))")
    )
