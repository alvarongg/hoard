"""SQLAlchemy model for application settings."""

from __future__ import annotations

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from api.models.base import Base


class AppSetting(Base):
    """Application settings model — key-value store for configuration."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    value: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AppSetting(key={self.key!r})>"
