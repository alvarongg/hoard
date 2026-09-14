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
    BACKUP_DIR: str = "/app/backups"
    # Directory holding the official catalog library (manifest.json + files).
    # Defaults to the repo's `catalogs/` dir mounted into the image.
    CATALOG_LIBRARY_DIR: str = "/app/catalogs"
    # Optional remote source: base URL that hosts manifest.json + catalog files
    # (e.g. a repo's raw.githubusercontent.com/<owner>/<repo>/<ref>/catalogs).
    # When set, the library is fetched over HTTPS instead of the local dir.
    CATALOG_LIBRARY_URL: str = ""
    # SSRF guard: only these hosts may be fetched for the remote library.
    CATALOG_LIBRARY_ALLOWED_HOSTS: str = "raw.githubusercontent.com"
    SEARCH_SIMILARITY_THRESHOLD: float = 0.3

    @cached_property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list of origin strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @cached_property
    def catalog_library_allowed_hosts_list(self) -> list[str]:
        """Parse CATALOG_LIBRARY_ALLOWED_HOSTS into a list of hostnames."""
        return [
            h.strip()
            for h in self.CATALOG_LIBRARY_ALLOWED_HOSTS.split(",")
            if h.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
