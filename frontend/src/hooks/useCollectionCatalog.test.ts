import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCollectionCatalog } from "./useCollectionCatalog";

const API_URL = "http://localhost:8000/api";

interface RawCatalog {
  id: string;
  sub_category_id: string;
  name: string;
  description: string | null;
  total_items: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

function rawCatalog(overrides: Partial<RawCatalog> = {}): RawCatalog {
  return {
    id: "catalog-1",
    sub_category_id: "sub-1",
    name: "N64 Games Catalog",
    description: null,
    total_items: 296,
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

function mockCatalogs(catalogs: RawCatalog[]) {
  server.use(
    http.get(`${API_URL}/catalogs`, () => HttpResponse.json(catalogs)),
  );
}

describe("useCollectionCatalog", () => {
  it("resolves the active catalog of the given sub-category", async () => {
    mockCatalogs([
      rawCatalog({ id: "catalog-other", sub_category_id: "sub-2" }),
      rawCatalog({ id: "catalog-1", sub_category_id: "sub-1" }),
    ]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog("sub-1"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogId).toBe("catalog-1");
    expect(result.current.catalog?.subCategoryId).toBe("sub-1");
  });

  it("returns null when the sub-category is null", async () => {
    mockCatalogs([rawCatalog()]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog(null), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogId).toBeNull();
    expect(result.current.catalog).toBeNull();
  });

  it("returns null when the sub-category is undefined", async () => {
    mockCatalogs([rawCatalog()]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog(undefined), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogId).toBeNull();
  });

  it("returns null when no catalog belongs to the sub-category", async () => {
    mockCatalogs([rawCatalog({ sub_category_id: "sub-99" })]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog("sub-1"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogId).toBeNull();
  });

  it("ignores inactive catalogs of the sub-category", async () => {
    mockCatalogs([
      rawCatalog({ id: "catalog-inactive", is_active: false }),
    ]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog("sub-1"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogId).toBeNull();
  });

  it("prefers the active catalog when the sub-category has both", async () => {
    mockCatalogs([
      rawCatalog({ id: "catalog-inactive", is_active: false }),
      rawCatalog({ id: "catalog-active", is_active: true }),
    ]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog("sub-1"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogId).toBe("catalog-active");
  });

  it("reports loading while catalogs are being fetched", () => {
    mockCatalogs([rawCatalog()]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog("sub-1"), {
      wrapper,
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.catalogId).toBeNull();
  });

  it("exposes the error and a null catalog when the request fails", async () => {
    server.use(
      http.get(`${API_URL}/catalogs`, () =>
        HttpResponse.json({ detail: "Boom" }, { status: 500 }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCollectionCatalog("sub-1"), {
      wrapper,
    });

    await waitFor(() => expect(result.current.error).not.toBeNull());

    expect(result.current.catalogId).toBeNull();
  });
});
