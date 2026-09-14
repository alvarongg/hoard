import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCollectionStats } from "./useCollectionStats";

const API_URL = "http://localhost:8000/api";

describe("useCollectionStats", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionStats("col-1"),
      { wrapper },
    );

    expect(result.current.isLoading).toBe(true);
  });

  it("fetches stats for a collection", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/stats`, () =>
        HttpResponse.json({
          total_items: 42,
          different_categories_count: 3,
          total_invested: 1500.5,
          current_value: 2200.0,
          value_gain: 699.5,
          roi_percentage: 46.63,
          complete_items: 38,
          graded_items: 5,
        }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionStats("col-1"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.totalItems).toBe(42);
    expect(result.current.data?.differentCategoriesCount).toBe(3);
    expect(result.current.data?.totalInvested).toBe(1500.5);
    expect(result.current.data?.currentValue).toBe(2200.0);
    expect(result.current.data?.valueGain).toBe(699.5);
    expect(result.current.data?.roiPercentage).toBeCloseTo(46.63);
    expect(result.current.data?.completeItems).toBe(38);
    expect(result.current.data?.gradedItems).toBe(5);
  });

  it("does not fetch when collectionId is undefined", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionStats(undefined),
      { wrapper },
    );

    // Should stay in idle state (not loading, not success)
    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/stats`, () =>
        HttpResponse.json({ detail: "Collection not found" }, { status: 404 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionStats("nonexistent"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });

  it("handles null ROI percentage", async () => {
    server.use(
      http.get(`${API_URL}/collections/:id/stats`, () =>
        HttpResponse.json({
          total_items: 0,
          different_categories_count: 0,
          total_invested: null,
          current_value: null,
          value_gain: null,
          roi_percentage: null,
          complete_items: 0,
          graded_items: 0,
        }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useCollectionStats("col-empty"),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.roiPercentage).toBeNull();
    expect(result.current.data?.totalInvested).toBeNull();
    expect(result.current.data?.totalItems).toBe(0);
  });
});
