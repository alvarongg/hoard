"""Tests for core.database module."""

import inspect

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from core.database import async_session_factory, engine, get_async_session


class TestDatabaseModule:
    def test_engine_is_async_engine(self) -> None:
        assert isinstance(engine, AsyncEngine)

    def test_session_factory_is_async_sessionmaker(self) -> None:
        assert isinstance(async_session_factory, async_sessionmaker)

    def test_get_async_session_is_async_generator(self) -> None:
        assert inspect.isasyncgenfunction(get_async_session)
