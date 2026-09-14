import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useSupplier } from "./useSuppliers";

const API_URL = "http://localhost:8000/api";

describe("useSupplier", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplier("supplier-1"), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("returns single supplier on success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplier("supplier-1"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(result.current.data?.name).toBe("GameStop");
    expect(result.current.data?.type).toBe("store");
    expect(result.current.data?.isFavorite).toBe(true);
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/suppliers/:id`, () =>
        HttpResponse.json({ detail: "Not found" }, { status: 404 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplier("not-found"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("is disabled when id is undefined", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSupplier(undefined), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(result.current.data).toBeUndefined();
  });
});
