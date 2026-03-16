"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+asyncpg://hoard:changeme@db:5432/hoard"
    SECRET_KEY: str = "change-this"
    CORS_ORIGINS: str = "http://localhost,http://localhost:3000"
    UPLOAD_DIR: str = "/app/uploads"

    @cached_property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list of origin strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
