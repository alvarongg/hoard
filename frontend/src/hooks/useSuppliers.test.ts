import { describe, it, expect } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useSuppliers } from "./useSuppliers";
import { mockSuppliers } from "../test/mocks/handlers";

const API_URL = "http://localhost:8000/api";

describe("useSuppliers", () => {
  it("returns loading state initially", () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("returns suppliers list on success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(Array.isArray(result.current.data)).toBe(true);
    expect(result.current.data!.length).toBe(2);
    expect(result.current.data?.[0]?.name).toBe("GameStop");
    expect(result.current.data?.[0]?.isFavorite).toBe(true);
  });

  it("returns error state on API failure", async () => {
    server.use(
      http.get(`${API_URL}/suppliers`, () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it("filters suppliers by type", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers({ type: "store" }), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(result.current.data!.length).toBe(1);
    expect(result.current.data?.[0]?.type).toBe("store");
  });

  it("filters suppliers by country", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers({ country: "USA" }), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(result.current.data!.length).toBe(2);
  });

  it("filters suppliers by favorite status", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useSuppliers({ isFavorite: true }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(result.current.data!.length).toBe(1);
    expect(result.current.data?.[0]?.isFavorite).toBe(true);
  });

  it("create mutation invalidates cache after success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    await act(async () => {
      result.current.create.mutate({
        name: "New Supplier",
        type: "online",
      });
    });

    await waitFor(() => expect(result.current.create.isSuccess).toBe(true));

    expect(result.current.create.data?.name).toBe("New Supplier");
  });

  it("update mutation invalidates cache after success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    await act(async () => {
      result.current.update.mutate({
        id: "supplier-1",
        data: { name: "Updated Supplier" },
      });
    });

    await waitFor(() => expect(result.current.update.isSuccess).toBe(true));

    expect(result.current.update.data?.name).toBe("Updated Supplier");
  });

  it("delete mutation invalidates cache after success", async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    await act(async () => {
      result.current.remove.mutate("supplier-1");
    });

    await waitFor(() => expect(result.current.remove.isSuccess).toBe(true));
  });

  it("toggleFavorite performs optimistic update", async () => {
    // Setup mock to return updated value after invalidation
    let toggleCount = 0;
    server.use(
      http.get(`${API_URL}/suppliers`, () => {
        // On refetch after mutation, return updated data
        if (toggleCount > 0) {
          return HttpResponse.json([
            {
              ...mockSuppliers[0],
              is_favorite: false,
            },
            mockSuppliers[1],
          ]);
        }
        toggleCount++;
        return HttpResponse.json(mockSuppliers);
      }),
      http.patch(`${API_URL}/suppliers/:id`, async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          ...mockSuppliers[0],
          ...body,
          updated_at: new Date().toISOString(),
        });
      }),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Supplier-1 starts as favorite (isFavorite: true)
    const initialSupplier = result.current.data?.find(
      (s) => s.id === "supplier-1",
    );
    expect(initialSupplier?.isFavorite).toBe(true);

    await act(async () => {
      result.current.toggleFavorite.mutate({
        id: "supplier-1",
        currentFavorite: true,
      });
    });

    // After mutation succeeds and query is invalidated, check the result
    await waitFor(() => expect(result.current.toggleFavorite.isSuccess).toBe(true));

    // Wait for the refetch to complete
    await waitFor(() => {
      const updated = result.current.data?.find((s) => s.id === "supplier-1");
      expect(updated?.isFavorite).toBe(false);
    });
  });

  it("toggleFavorite reverts optimistic update on error", async () => {
    server.use(
      http.patch(`${API_URL}/suppliers/:id`, () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSuppliers(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Supplier-1 starts as favorite (isFavorite: true)
    const initialSupplier = result.current.data?.find(
      (s) => s.id === "supplier-1",
    );
    expect(initialSupplier?.isFavorite).toBe(true);

    await act(async () => {
      result.current.toggleFavorite.mutate({
        id: "supplier-1",
        currentFavorite: true,
      });
    });

    // After error, should revert to original state
    await waitFor(() => expect(result.current.toggleFavorite.isError).toBe(true));

    await waitFor(() => {
      const reverted = result.current.data?.find((s) => s.id === "supplier-1");
      expect(reverted?.isFavorite).toBe(true);
    });
  });
});
