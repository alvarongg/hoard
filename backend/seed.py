"""Seed the database with initial categories and subcategories."""

from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings

logger = logging.getLogger(__name__)

SEED_DATA: dict[str, dict[str, str | list[dict[str, str]]]] = {
    "Videojuegos": {
        "slug": "videojuegos",
        "description": "Consolas, juegos y accesorios de videojuegos",
        "icon": "🎮",
        "subcategories": [
            {"name": "Famicom", "slug": "famicom", "description": "Nintendo Famicom / NES"},
            {"name": "Super Famicom", "slug": "super-famicom", "description": "Super Famicom / SNES"},
            {"name": "Nintendo 64", "slug": "nintendo-64", "description": "Nintendo 64"},
            {"name": "GameCube", "slug": "gamecube", "description": "Nintendo GameCube"},
            {"name": "PlayStation", "slug": "playstation", "description": "Sony PlayStation"},
            {"name": "PlayStation 2", "slug": "playstation-2", "description": "Sony PlayStation 2"},
            {"name": "Sega Genesis", "slug": "sega-genesis", "description": "Sega Genesis / Mega Drive"},
            {"name": "Game Boy", "slug": "game-boy", "description": "Nintendo Game Boy / Color / Advance"},
        ],
    },
    "Música": {
        "slug": "musica",
        "description": "Vinilos, CDs, cassettes y más",
        "icon": "🎵",
        "subcategories": [
            {"name": "Vinilos", "slug": "vinilos", "description": "Discos de vinilo"},
            {"name": "CDs", "slug": "cds", "description": "Discos compactos"},
            {"name": "Cassettes", "slug": "cassettes", "description": "Cintas de cassette"},
        ],
    },
    "Libros": {
        "slug": "libros",
        "description": "Libros, cómics, manga y revistas",
        "icon": "📚",
        "subcategories": [
            {"name": "Manga", "slug": "manga", "description": "Manga japonés"},
            {"name": "Cómics", "slug": "comics", "description": "Cómics americanos y europeos"},
            {"name": "Novelas", "slug": "novelas", "description": "Novelas y literatura"},
        ],
    },
    "TCG": {
        "slug": "tcg",
        "description": "Trading Card Games y cartas coleccionables",
        "icon": "🃏",
        "subcategories": [
            {"name": "Pokémon TCG", "slug": "pokemon-tcg", "description": "Cartas Pokémon"},
            {"name": "Magic: The Gathering", "slug": "mtg", "description": "Cartas Magic"},
            {"name": "Yu-Gi-Oh!", "slug": "yugioh", "description": "Cartas Yu-Gi-Oh!"},
        ],
    },
    "Figuras": {
        "slug": "figuras",
        "description": "Figuras de acción, estatuas y coleccionables",
        "icon": "🗿",
        "subcategories": [
            {"name": "Figuras de Acción", "slug": "figuras-accion", "description": "Figuras articuladas"},
            {"name": "Funko Pop", "slug": "funko-pop", "description": "Figuras Funko Pop"},
            {"name": "Amiibo", "slug": "amiibo", "description": "Figuras Nintendo Amiibo"},
        ],
    },
}


def _is_postgres(url: str) -> bool:
    """Check if the database URL points to PostgreSQL."""
    return "postgresql" in url


async def seed_database(engine: object | None = None) -> None:
    """Seed the database with initial categories and subcategories.

    Uses raw SQL with UUID casting for PostgreSQL compatibility.
    The schema.sql creates tables with native UUID columns, but ORM
    models use String(36), so we use raw SQL to handle the cast.

    Args:
        engine: Optional engine override (used in tests with SQLite).
    """
    if engine is None:
        settings = get_settings()
        engine = create_async_engine(settings.DATABASE_URL)

    is_pg = _is_postgres(str(engine.url))

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check what's already seeded
        cat_result = await session.execute(text("SELECT COUNT(*) FROM main_categories"))
        cat_count = cat_result.scalar() or 0

        sub_result = await session.execute(text("SELECT COUNT(*) FROM sub_categories"))
        sub_count = sub_result.scalar() or 0

        if cat_count > 0 and sub_count > 0:
            logger.info(
                "Database already seeded (%d categories, %d subcategories). Skipping.",
                cat_count,
                sub_count,
            )
            return

        need_categories = cat_count == 0
        need_subcategories = sub_count == 0

        if need_categories:
            logger.info("Seeding %d main categories...", len(SEED_DATA))
        if need_subcategories:
            logger.info("Seeding subcategories...")

        for sort_order, (name, data) in enumerate(SEED_DATA.items()):
            cat_id: str | None = None

            if need_categories:
                cat_id = str(uuid.uuid4())
                if is_pg:
                    await session.execute(
                        text(
                            "INSERT INTO main_categories (id, name, slug, description, icon, sort_order, created_at, updated_at) "
                            "VALUES (CAST(:id AS UUID), :name, :slug, :description, :icon, :sort_order, NOW(), NOW())"
                        ),
                        {
                            "id": cat_id,
                            "name": name,
                            "slug": data["slug"],
                            "description": data["description"],
                            "icon": data.get("icon", ""),
                            "sort_order": sort_order,
                        },
                    )
                else:
                    await session.execute(
                        text(
                            "INSERT INTO main_categories (id, name, slug, description, icon, sort_order, created_at, updated_at) "
                            "VALUES (:id, :name, :slug, :description, :icon, :sort_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                        ),
                        {
                            "id": cat_id,
                            "name": name,
                            "slug": data["slug"],
                            "description": data["description"],
                            "icon": data.get("icon", ""),
                            "sort_order": sort_order,
                        },
                    )
            elif need_subcategories:
                # Categories exist but subcategories don't — look up the existing category id
                row = await session.execute(
                    text("SELECT id FROM main_categories WHERE slug = :slug"),
                    {"slug": data["slug"]},
                )
                result_row = row.first()
                if result_row:
                    cat_id = str(result_row[0])

            if cat_id is None:
                continue

            if need_subcategories:
                subcategories = data.get("subcategories", [])
                for sub_order, sub in enumerate(subcategories):
                    sub_id = str(uuid.uuid4())

                    if is_pg:
                        await session.execute(
                            text(
                                "INSERT INTO sub_categories (id, main_category_id, name, slug, description, sort_order, created_at, updated_at) "
                                "VALUES (CAST(:id AS UUID), CAST(:main_category_id AS UUID), :name, :slug, :description, :sort_order, NOW(), NOW())"
                            ),
                            {
                                "id": sub_id,
                                "main_category_id": cat_id,
                                "name": sub["name"],
                                "slug": sub["slug"],
                                "description": sub.get("description", ""),
                                "sort_order": sub_order,
                            },
                        )
                    else:
                        await session.execute(
                            text(
                                "INSERT INTO sub_categories (id, main_category_id, name, slug, description, sort_order, created_at, updated_at) "
                                "VALUES (:id, :main_category_id, :name, :slug, :description, :sort_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                            ),
                            {
                                "id": sub_id,
                                "main_category_id": cat_id,
                                "name": sub["name"],
                                "slug": sub["slug"],
                                "description": sub.get("description", ""),
                                "sort_order": sub_order,
                            },
                        )

        await session.commit()
        logger.info("Seeding complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_database())
