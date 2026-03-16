"""Tests for core.config Settings."""

import pytest

from core.config import Settings, get_settings


class TestSettings:
    def test_default_database_url_uses_asyncpg(self) -> None:
        settings = Settings()
        assert "asyncpg" in settings.DATABASE_URL

    def test_default_secret_key_is_placeholder(self) -> None:
        settings = Settings()
        assert settings.SECRET_KEY == "change-this"

    def test_default_cors_origins_includes_localhost(self) -> None:
        settings = Settings()
        origins = settings.cors_origins_list
        assert "http://localhost" in origins
        assert "http://localhost:3000" in origins

    def test_default_upload_dir(self) -> None:
        settings = Settings()
        assert settings.UPLOAD_DIR == "/app/uploads"

    def test_get_settings_returns_settings_instance(self) -> None:
        result = get_settings()
        assert isinstance(result, Settings)

    def test_settings_from_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SECRET_KEY", "my-secret")
        settings = Settings()
        assert settings.SECRET_KEY == "my-secret"

    def test_cors_origins_from_comma_separated_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost,http://example.com")
        settings = Settings()
        assert settings.cors_origins_list == ["http://localhost", "http://example.com"]

    def test_cors_origins_single_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost")
        settings = Settings()
        assert settings.cors_origins_list == ["http://localhost"]

    def test_cors_origins_strips_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CORS_ORIGINS", " http://a.com , http://b.com ")
        settings = Settings()
        assert settings.cors_origins_list == ["http://a.com", "http://b.com"]
