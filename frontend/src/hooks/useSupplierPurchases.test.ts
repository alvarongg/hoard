import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useSupplierPurchases } from "./useSuppliers";

const API_URL = "http://localhost:8000/api";

describe("useSupplierPurchases", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplierPurchases("supplier-1"), {
      wrapper,
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("returns purchases list on success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplierPurchases("supplier-1"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
    expect(result.current.data!.length).toBe(1);
    expect(result.current.data?.[0]?.purchasePrice).toBe(45.0);
    expect(result.current.data?.[0]?.purchaseCurrency).toBe("USD");
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/suppliers/:id/purchases`, () =>
        HttpResponse.json({ detail: "Not found" }, { status: 404 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplierPurchases("not-found"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("is disabled when id is undefined", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplierPurchases(undefined), {
      wrapper,
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it("returns empty array when supplier has no purchases", async () => {
    server.use(
      http.get(`${API_URL}/suppliers/:id/purchases`, () =>
        HttpResponse.json([]),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplierPurchases("supplier-2"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(result.current.data!.length).toBe(0);
  });
});
