"""SQLAlchemy models for main categories and sub-categories."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import DBUUID, Base, TimestampMixin, UUIDMixin


class MainCategory(UUIDMixin, TimestampMixin, Base):
    """Main category model (e.g., Videojuegos, Música, Libros, TCG)."""

    __tablename__ = "main_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    sub_categories: Mapped[list[SubCategory]] = relationship(
        back_populates="main_category",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<MainCategory(id={self.id!r}, name={self.name!r})>"


class SubCategory(UUIDMixin, TimestampMixin, Base):
    """Sub-category model (e.g., Consolas, Juegos, Vinilos, CDs)."""

    __tablename__ = "sub_categories"
    __table_args__ = (
        UniqueConstraint("main_category_id", "slug", name="uq_sub_category_main_slug"),
    )

    main_category_id: Mapped[str] = mapped_column(
        DBUUID(),
        ForeignKey("main_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    main_category: Mapped[MainCategory] = relationship(
        back_populates="sub_categories",
    )

    def __repr__(self) -> str:
        return f"<SubCategory(id={self.id!r}, name={self.name!r})>"
