import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCollectionItems } from "./useCollectionItems";

const API_URL = "http://localhost:8000/api";

describe("useCollectionItems", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItems("col-1"),
      { wrapper },
    );

    expect(result.current.isLoading).toBe(true);
  });

  it("fetches items filtered by collectionId", async () => {
    let capturedUrl = "";

    server.use(
      http.get(`${API_URL}/collections/:id/items`, ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json([
          {
            id: "item-1",
            collection_id: "col-1",
            catalog_item_id: "cat-item-1",
            condition: "excellent",
            is_complete: true,
            notes: null,
            purchase_price: 45.0,
            purchase_currency: "USD",
            purchase_date: null,
            acquisition_type: "purchase",
            storage_location: null,
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T00:00:00Z",
          },
        ]);
      }),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItems("col-1"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(capturedUrl).toContain("/collections/col-1/items");
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0]?.collectionId).toBe("col-1");
  });

  it("does not fetch when collectionId is empty", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItems(""),
      { wrapper },
    );

    // Should stay in idle state (not loading, not success)
    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/items`, () =>
        HttpResponse.json({ detail: "Not found" }, { status: 404 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItems("col-1"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });
});
