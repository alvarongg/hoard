"""Unit tests for the on-demand PriceCharting price lookup (no network)."""

from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.models import (
    Base,
    Catalog,
    CatalogItem,
    MainCategory,
    SubCategory,
)
from api.models.price_history import CatalogPriceHistory
from api.services.price_lookup_service import (
    PriceChartingClient,
    PriceLookupService,
)
from core.exceptions import (
    NotFoundError,
    ToolUnavailableError,
    ValidationError,
)

pytestmark = pytest.mark.asyncio

_ALLOWED = ["pricecharting.com", "www.pricecharting.com"]
_HTML = """
<table>
  <td id="used_price"><span class="price js-price">$12.34</span></td>
  <td id="complete_price"><span class="price js-price">$45.00</span></td>
  <td id="new_price"><span class="price js-price">$120.50</span></td>
</table>
"""


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.create_all)
    session = AsyncSession(engine, expire_on_commit=False)
    async with session:
        yield session
    await engine.dispose()


async def _seed_catalog_item(db: AsyncSession) -> CatalogItem:
    main = MainCategory(name="Videojuegos", slug="videojuegos")
    db.add(main)
    await db.flush()
    sub = SubCategory(main_category_id=main.id, name="Famicom", slug="famicom")
    db.add(sub)
    await db.flush()
    catalog = Catalog(sub_category_id=sub.id, name="Famicom Games")
    db.add(catalog)
    await db.flush()
    item = CatalogItem(catalog_id=catalog.id, title="Dennou Kyusei Uranai")
    db.add(item)
    await db.commit()
    return item


async def test_client_parses_prices() -> None:
    client = PriceChartingClient(_ALLOWED)
    prices = client.parse_prices(_HTML)
    assert (("good", False, Decimal("12.34")) in prices)
    assert (("good", True, Decimal("45.00")) in prices)
    assert (("mint", True, Decimal("120.50")) in prices)


async def test_client_rejects_non_https() -> None:
    client = PriceChartingClient(_ALLOWED)
    with pytest.raises(ValidationError):
        client.fetch("http://www.pricecharting.com/game/famicom/x")


async def test_client_rejects_host_not_in_allowlist() -> None:
    client = PriceChartingClient(_ALLOWED)
    with pytest.raises(ValidationError):
        client.fetch("https://evil.example.com/game/x")


async def test_lookup_persists_price_history(
    db: AsyncSession, monkeypatch
) -> None:
    item = await _seed_catalog_item(db)
    client = PriceChartingClient(_ALLOWED)
    monkeypatch.setattr(client, "fetch", lambda url: _HTML)
    svc = PriceLookupService(db, client, enabled=True)

    url = "https://www.pricecharting.com/game/famicom/dennou-kyusei-uranai"
    created = await svc.lookup(item.id, url)
    assert len(created) == 3
    rows = (
        await db.execute(
            select(CatalogPriceHistory).where(
                CatalogPriceHistory.catalog_item_id == item.id
            )
        )
    ).scalars().all()
    assert len(rows) == 3
    assert all(r.source == "PriceCharting" for r in rows)
    assert all(r.source_url == url for r in rows)


async def test_lookup_disabled_raises(db: AsyncSession) -> None:
    item = await _seed_catalog_item(db)
    client = PriceChartingClient(_ALLOWED)
    svc = PriceLookupService(db, client, enabled=False)
    with pytest.raises(ToolUnavailableError):
        await svc.lookup(item.id, "https://www.pricecharting.com/x")


async def test_lookup_unknown_item_raises(db: AsyncSession, monkeypatch) -> None:
    client = PriceChartingClient(_ALLOWED)
    monkeypatch.setattr(client, "fetch", lambda url: _HTML)
    svc = PriceLookupService(db, client, enabled=True)
    with pytest.raises(NotFoundError):
        await svc.lookup("00000000-0000-0000-0000-000000000000",
                         "https://www.pricecharting.com/x")
