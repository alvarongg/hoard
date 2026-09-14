import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useAccessories, useLowStock } from "./useAccessories";

const API_URL = "http://localhost:8000/api";

const acc = {
  id: "a1",
  name: "Case",
  category: null,
  subcategory: null,
  compatible_sub_categories: null,
  size_specifications: null,
  quantity_total: 10,
  quantity_in_use: 0,
  quantity_available: 10,
  is_low_stock: false,
  minimum_stock_alert: 5,
  reorder_quantity: null,
  unit_cost: null,
  currency: "USD",
  supplier_id: null,
  supplier_sku: null,
  supplier_url: null,
  notes: null,
};

describe("useAccessories", () => {
  it("returns accessories on success", async () => {
    server.use(
      http.get(`${API_URL}/accessories`, () => HttpResponse.json([acc])),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useAccessories(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.quantityAvailable).toBe(10);
  });

  it("surfaces error", async () => {
    server.use(
      http.get(`${API_URL}/accessories`, () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useAccessories(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe("useLowStock", () => {
  it("returns low-stock entries", async () => {
    server.use(
      http.get(`${API_URL}/accessories/low-stock`, () =>
        HttpResponse.json([
          {
            id: "a1",
            name: "Case",
            quantity_available: 1,
            minimum_stock_alert: 5,
            reorder_quantity: 10,
          },
        ]),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLowStock(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.name).toBe("Case");
  });
});
