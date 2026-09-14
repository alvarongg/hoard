"""On-demand price lookup against PriceCharting.

By design this is SINGLE-ITEM and USER-TRIGGERED only: there is no bulk or
scheduled refresh. A successful lookup is stored as one price-history record
(source="PriceCharting") whose price_date is the day of the lookup, so the
history reflects only what the collector actively queried.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.catalog import CatalogItem
from api.schemas.price_history import PriceHistoryCreate
from api.services.price_history_service import PriceHistoryService
from core.exceptions import (
    NotFoundError,
    ToolUnavailableError,
    ValidationError,
)

_HTTP_TIMEOUT = 20
_MAX_BYTES = 3 * 1024 * 1024
# PriceCharting renders prices in cells like: id="used_price" ... $12.34
_PRICE_RE = re.compile(
    r'id="(used_price|complete_price|new_price)"[^$]*\$'
    r"([0-9][0-9,]*\.?[0-9]{0,2})",
    re.IGNORECASE | re.DOTALL,
)
_CONDITION_BY_CELL = {
    "used_price": ("good", False),
    "complete_price": ("good", True),
    "new_price": ("mint", True),
}


class PriceChartingClient:
    """Fetches and parses a single PriceCharting item page over HTTPS."""

    def __init__(self, allowed_hosts: list[str]) -> None:
        self._allowed = {h.strip().lower() for h in allowed_hosts if h.strip()}

    def _validate_url(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            raise ValidationError("Price lookup URL must use https")
        if (parsed.hostname or "").lower() not in self._allowed:
            raise ValidationError(
                f"Host '{parsed.hostname}' is not in the price lookup allowlist"
            )

    def fetch(self, url: str) -> str:
        self._validate_url(url)
        req = urllib.request.Request(
            url, headers={"User-Agent": "HoardPriceLookup/1.0"}
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - scheme/host checked
                req, timeout=_HTTP_TIMEOUT
            ) as resp:
                return resp.read(_MAX_BYTES).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise NotFoundError("Item not found on PriceCharting") from exc
            raise ToolUnavailableError(
                f"PriceCharting returned HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ToolUnavailableError(
                f"Could not reach PriceCharting: {exc.reason}"
            ) from exc

    @staticmethod
    def parse_prices(html: str) -> list[tuple[str, bool, Decimal]]:
        """Return [(condition, is_complete, price)] found on the page."""
        out: list[tuple[str, bool, Decimal]] = []
        for cell, raw in _PRICE_RE.findall(html):
            condition, is_complete = _CONDITION_BY_CELL[cell.lower()]
            price = Decimal(raw.replace(",", ""))
            out.append((condition, is_complete, price))
        return out


class PriceLookupService:
    """Orchestrates an on-demand lookup and stores the result."""

    def __init__(
        self,
        db: AsyncSession,
        client: PriceChartingClient,
        *,
        enabled: bool = True,
    ) -> None:
        self._db = db
        self._client = client
        self._enabled = enabled
        self._prices = PriceHistoryService(db)

    async def lookup(self, catalog_item_id: str, url: str) -> list:
        """Fetch prices for one item and persist them as price history."""
        if not self._enabled:
            raise ToolUnavailableError("Price lookup is disabled")
        catalog_item = await self._db.get(CatalogItem, catalog_item_id)
        if catalog_item is None:
            raise NotFoundError(f"Catalog item '{catalog_item_id}' not found")

        html = self._client.fetch(url)
        found = self._client.parse_prices(html)
        if not found:
            raise ValidationError(
                "Could not read any price from the PriceCharting page"
            )

        today = date.today()
        created = []
        for condition, is_complete, price in found:
            data = PriceHistoryCreate(
                condition=condition,
                is_complete=is_complete,
                price=price,
                currency="USD",
                source="PriceCharting",
                source_url=url,
                price_date=today,
            )
            try:
                created.append(
                    await self._prices.create(catalog_item_id, data)
                )
            except Exception:  # noqa: BLE001 - skip same-day duplicates
                continue
        return created
