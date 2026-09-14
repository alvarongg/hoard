import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import {
  useDashboardStats,
  useValuationStats,
  useCategoryStats,
} from "./useStats";

const API_URL = "http://localhost:8000/api";

describe("useStats hooks", () => {
  it("useDashboardStats returns data", async () => {
    server.use(
      http.get(`${API_URL}/stats/dashboard`, () =>
        HttpResponse.json({
          total_collections: 1,
          total_items: 5,
          total_invested: "100.00",
          current_value: "150.00",
          value_gain: "50.00",
          roi_percentage: "50.00",
          complete_items: 2,
          graded_items: 1,
        }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useDashboardStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.totalItems).toBe(5);
  });

  it("useValuationStats surfaces error", async () => {
    server.use(
      http.get(`${API_URL}/stats/valuation`, () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useValuationStats(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it("useCategoryStats returns list", async () => {
    server.use(
      http.get(`${API_URL}/stats/categories`, () =>
        HttpResponse.json([
          {
            sub_category_id: "s1",
            sub_category_name: "N64",
            item_count: 2,
            current_value: "80.00",
          },
        ]),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCategoryStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.subCategoryName).toBe("N64");
  });
});
