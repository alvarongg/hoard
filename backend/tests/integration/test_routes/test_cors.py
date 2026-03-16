"""Integration tests for CORS middleware configuration."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
class TestCORSMiddleware:
    async def test_cors_allows_configured_origin(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    async def test_cors_rejects_unknown_origin(self) -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.options(
                "/health",
                headers={
                    "Origin": "http://evil.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert "access-control-allow-origin" not in response.headers
