import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import {
  usePriceHistory,
  useLatestPrices,
  useRefreshMarketValue,
} from "./usePriceHistory";

const API_URL = "http://localhost:8000/api";
const CATALOG_ITEM_ID = "cat-item-1";
const COLLECTION_ITEM_ID = "coll-item-1";

const priceRecord = {
  id: "ph-1",
  catalog_item_id: CATALOG_ITEM_ID,
  condition: "good",
  is_complete: true,
  completeness_description: null,
  price: "50.00",
  currency: "USD",
  source: "eBay",
  source_url: null,
  price_date: "2026-01-01",
  region: null,
  notes: null,
  recorded_at: "2026-01-01T00:00:00Z",
};

describe("usePriceHistory", () => {
  it("returns price records on success", async () => {
    server.use(
      http.get(
        `${API_URL}/catalog-items/${CATALOG_ITEM_ID}/price-history`,
        () => HttpResponse.json([priceRecord]),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => usePriceHistory(CATALOG_ITEM_ID), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.price).toBe("50.00");
    expect(result.current.data?.[0]?.catalogItemId).toBe(CATALOG_ITEM_ID);
  });

  it("surfaces error state", async () => {
    server.use(
      http.get(
        `${API_URL}/catalog-items/${CATALOG_ITEM_ID}/price-history`,
        () => HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => usePriceHistory(CATALOG_ITEM_ID), {
      wrapper,
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it("is disabled without a catalog item id", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => usePriceHistory(undefined), {
      wrapper,
    });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useLatestPrices", () => {
  it("returns latest prices", async () => {
    server.use(
      http.get(
        `${API_URL}/catalog-items/${CATALOG_ITEM_ID}/price-history/latest`,
        () =>
          HttpResponse.json([
            {
              condition: "good",
              is_complete: true,
              price: "50.00",
              currency: "USD",
              price_date: "2026-01-01",
              source: "eBay",
            },
          ]),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLatestPrices(CATALOG_ITEM_ID), {
      wrapper,
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.condition).toBe("good");
  });
});

describe("useRefreshMarketValue", () => {
  it("returns update result on mutate", async () => {
    server.use(
      http.post(
        `${API_URL}/collection-items/${COLLECTION_ITEM_ID}/refresh-value`,
        () =>
          HttpResponse.json({
            updated: true,
            current_market_value: "75.00",
            value_source: "eBay",
            reason: null,
          }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useRefreshMarketValue(COLLECTION_ITEM_ID),
      { wrapper },
    );
    const res = await result.current.mutateAsync();
    expect(res.updated).toBe(true);
    expect(res.currentMarketValue).toBe("75.00");
  });
});
