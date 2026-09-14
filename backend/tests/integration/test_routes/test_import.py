"""Integration tests for JSON import REST endpoints."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db
from api.models.base import Base
from api.models.collection import Collection
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
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _envelope() -> bytes:
    return json.dumps(
        {
            "schema_version": "1.0",
            "entity_type": "collection",
            "exported_at": "2026-01-01T00:00:00Z",
            "collection": {"name": "Imported", "collection_type": "mixed"},
            "items": [],
        }
    ).encode("utf-8")


@pytest.mark.asyncio
async def test_preview_200_and_no_write(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/import/preview",
        files={"file": ("export.json", _envelope(), "application/json")},
    )
    assert resp.status_code == 200
    assert resp.json()["to_create"] == 1
    # No execute call -> DB stays empty
    async with _TestSessionFactory() as s:
        count = (
            await s.execute(select(func.count()).select_from(Collection))
        ).scalar()
    assert count == 0


@pytest.mark.asyncio
async def test_execute_200(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/import/execute",
        files={"file": ("export.json", _envelope(), "application/json")},
    )
    assert resp.status_code == 200
    assert resp.json()["created_count"] == 1


@pytest.mark.asyncio
async def test_invalid_json_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/import/preview",
        files={"file": ("bad.json", b"{not json", "application/json")},
    )
    assert resp.status_code == 422
