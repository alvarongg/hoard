import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useTransactions, useItemInvestment } from "./useTransactions";

const API_URL = "http://localhost:8000/api";
const ITEM = "ci-1";

const tx = {
  id: "t1",
  collection_item_id: ITEM,
  transaction_type: "purchase",
  transaction_date: "2026-01-01",
  amount: "100.00",
  currency: "USD",
  shipping_cost: "10.00",
  tax_amount: null,
  other_fees: null,
  total_amount: "110.00",
  supplier_id: null,
  counterpart_name: null,
  invoice_number: null,
  receipt_path: null,
  payment_method: null,
  notes: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("useTransactions", () => {
  it("returns transactions on success", async () => {
    server.use(
      http.get(`${API_URL}/collection-items/${ITEM}/transactions`, () =>
        HttpResponse.json([tx]),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useTransactions(ITEM), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.totalAmount).toBe("110.00");
  });

  it("surfaces error state", async () => {
    server.use(
      http.get(`${API_URL}/collection-items/${ITEM}/transactions`, () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useTransactions(ITEM), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe("useItemInvestment", () => {
  it("returns investment summary", async () => {
    server.use(
      http.get(`${API_URL}/collection-items/${ITEM}/investment`, () =>
        HttpResponse.json({
          real_invested: "100.00",
          total_outflow: "100.00",
          total_inflow: "0",
          current_market_value: null,
          roi_percentage: null,
          source: "transactions",
        }),
      ),
    );
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useItemInvestment(ITEM), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.source).toBe("transactions");
    expect(result.current.data?.roiPercentage).toBeNull();
  });
});
