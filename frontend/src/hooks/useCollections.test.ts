import { describe, it, expect } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCollections } from "./useCollections";

const API_URL = "http://localhost:8000/api";

describe("useCollections", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollections(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("returns collections list on success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollections(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
    expect(result.current.data!.length).toBeGreaterThan(0);
    expect(result.current.data?.[0]?.name).toBe("My N64 Collection");
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/collections`, () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollections(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("create mutation invalidates cache after success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollections(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const initialData = result.current.data;

    server.use(
      http.get(`${API_URL}/collections`, () =>
        HttpResponse.json([
          {
            id: "col-1",
            name: "My N64 Collection",
            collection_type: "single_category",
            is_active: true,
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T00:00:00Z",
            description: null,
            theme: null,
            theme_description: null,
            restricted_to_sub_category_id: "sub-1",
            goal_description: null,
            goal_items_count: null,
            display_order: "custom",
            is_public: false,
          },
          {
            id: "col-2",
            name: "New Collection",
            collection_type: "multi_category",
            is_active: true,
            created_at: "2024-01-02T00:00:00Z",
            updated_at: "2024-01-02T00:00:00Z",
            description: null,
            theme: null,
            theme_description: null,
            restricted_to_sub_category_id: null,
            goal_description: null,
            goal_items_count: null,
            display_order: "custom",
            is_public: false,
          },
        ]),
      ),
    );

    await act(async () => {
      result.current.create.mutate({
        name: "New Collection",
        collectionType: "multi_category",
      });
    });

    await waitFor(() => expect(result.current.create.isSuccess).toBe(true));

    // After mutation, the query should be refetched
    await waitFor(() => {
      expect(result.current.data?.length).toBe(2);
    });

    expect(result.current.data?.length).not.toBe(initialData?.length);
  });
});
