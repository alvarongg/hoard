import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCollectionItemsGrouped } from "./useCollectionItemsGrouped";

const API_URL = "http://localhost:8000/api";

describe("useCollectionItemsGrouped", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItemsGrouped("col-1"),
      { wrapper },
    );

    expect(result.current.isLoading).toBe(true);
  });

  it("fetches grouped items for a collection", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/items/grouped`, () =>
        HttpResponse.json([
          {
            main_category_id: "cat-1",
            main_category_name: "Video Games",
            sub_category_id: "sub-1",
            sub_category_name: "Nintendo 64",
            item_count: 25,
          },
          {
            main_category_id: "cat-1",
            main_category_name: "Video Games",
            sub_category_id: "sub-2",
            sub_category_name: "PlayStation 2",
            item_count: 17,
          },
        ]),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItemsGrouped("col-1"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0]?.mainCategoryName).toBe("Video Games");
    expect(result.current.data?.[0]?.subCategoryName).toBe("Nintendo 64");
    expect(result.current.data?.[0]?.itemCount).toBe(25);
    expect(result.current.data?.[1]?.itemCount).toBe(17);
  });

  it("does not fetch when collectionId is undefined", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItemsGrouped(undefined),
      { wrapper },
    );

    // Should stay in idle state (not loading, not success)
    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/items/grouped`, () =>
        HttpResponse.json({ detail: "Collection not found" }, { status: 404 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItemsGrouped("nonexistent"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });

  it("returns empty array for collection with no items", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/items/grouped`, () =>
        HttpResponse.json([]),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItemsGrouped("col-empty"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });

  it("handles groups with null category (mixed collection)", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/items/grouped`, () =>
        HttpResponse.json([
          {
            main_category_id: null,
            main_category_name: null,
            sub_category_id: "sub-1",
            sub_category_name: "Unknown Category",
            item_count: 5,
          },
        ]),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionItemsGrouped("col-mixed"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0]?.mainCategoryId).toBeNull();
    expect(result.current.data?.[0]?.mainCategoryName).toBeNull();
    expect(result.current.data?.[0]?.itemCount).toBe(5);
  });
});
