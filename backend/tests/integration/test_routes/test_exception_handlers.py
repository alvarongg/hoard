"""Integration tests for global exception handlers.

Registers temporary test routes that raise each domain exception,
then verifies the correct HTTP status code and response body.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from core.exceptions import (
    DuplicateError,
    FileValidationError,
    NotFoundError,
    ValidationError,
)
from main import app


# ---------------------------------------------------------------------------
# Register temporary test routes that raise domain exceptions
# ---------------------------------------------------------------------------

@app.get("/_test/not-found")
async def _raise_not_found() -> None:
    raise NotFoundError("Resource not found")


@app.get("/_test/duplicate")
async def _raise_duplicate() -> None:
    raise DuplicateError("Resource already exists")


@app.get("/_test/validation")
async def _raise_validation() -> None:
    raise ValidationError("Invalid business rule")


@app.get("/_test/file-validation")
async def _raise_file_validation() -> None:
    raise FileValidationError("File type not allowed")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNotFoundHandler:
    async def test_returns_404_with_detail(self, client: AsyncClient) -> None:
        response = await client.get("/_test/not-found")
        assert response.status_code == 404
        assert response.json() == {"detail": "Resource not found"}


class TestDuplicateHandler:
    async def test_returns_409_with_detail(self, client: AsyncClient) -> None:
        response = await client.get("/_test/duplicate")
        assert response.status_code == 409
        assert response.json() == {"detail": "Resource already exists"}


class TestValidationHandler:
    async def test_returns_422_with_detail(self, client: AsyncClient) -> None:
        response = await client.get("/_test/validation")
        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid business rule"}


class TestFileValidationHandler:
    async def test_returns_422_with_detail(self, client: AsyncClient) -> None:
        response = await client.get("/_test/file-validation")
        assert response.status_code == 422
        assert response.json() == {"detail": "File type not allowed"}
