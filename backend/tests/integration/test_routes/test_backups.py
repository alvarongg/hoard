"""Integration tests for backup REST endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_backup_service, get_db
from api.models.base import Base
from api.services.backup_service import BackupService
from main import app


_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_TestSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionFactory() as session:
        yield session


@pytest.fixture(autouse=True)
async def _setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client(tmp_path) -> AsyncGenerator[AsyncClient, None]:
    backup_dir = str(tmp_path / "backups")

    async def _override_service() -> AsyncGenerator[BackupService, None]:
        async with _TestSessionFactory() as session:
            yield BackupService(session, backup_dir, "postgresql://x/y")

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_backup_service] = _override_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_empty_200(client: AsyncClient) -> None:
    resp = await client.get("/api/backups")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_without_pg_dump_503(client: AsyncClient, monkeypatch) -> None:
    # pg_dump is not installed in the test environment -> 503.
    monkeypatch.setattr(
        "api.services.backup_service.shutil.which", lambda name: None
    )
    resp = await client.post("/api/backups")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_config_get_and_put(client: AsyncClient) -> None:
    resp = await client.get("/api/backups/config")
    assert resp.status_code == 200
    assert resp.json()["frequency"] == "weekly"

    resp2 = await client.put(
        "/api/backups/config",
        json={"frequency": "daily", "retention_count": 10},
    )
    assert resp2.status_code == 200
    assert resp2.json()["retention_count"] == 10


@pytest.mark.asyncio
async def test_config_invalid_retention_422(client: AsyncClient) -> None:
    resp = await client.put(
        "/api/backups/config", json={"retention_count": 0}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_download_unknown_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/backups/hoard-backup-{uuid4().hex}.tar.gz/download")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_restore_unknown_404(client: AsyncClient) -> None:
    resp = await client.post(
        f"/api/backups/hoard-backup-{uuid4().hex}.tar.gz/restore"
    )
    assert resp.status_code == 404
