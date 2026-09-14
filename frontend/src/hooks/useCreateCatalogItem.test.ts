import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { mockCatalogItem } from "../test/mocks/handlers";
import { useCreateCatalogItem } from "./useCreateCatalogItem";

const API_URL = "http://localhost:8000/api";
const CATALOG_ID = "catalog-1";

describe("useCreateCatalogItem", () => {
  it("posts to the catalog items endpoint with snake_case body", async () => {
    let capturedUrl = "";
    let capturedMethod = "";
    let capturedBody: Record<string, unknown> = {};

    server.use(
      http.post(`${API_URL}/catalogs/:id/items`, async ({ request }) => {
        capturedUrl = request.url;
        capturedMethod = request.method;
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          { ...mockCatalogItem, ...capturedBody },
          { status: 201 },
        );
      }),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCreateCatalogItem(CATALOG_ID), {
      wrapper,
    });

    await act(async () => {
      result.current.mutate({
        title: "Super Mario 64",
        coverImageUrl: "https://example.com/sm64.jpg",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(capturedMethod).toBe("POST");
    expect(capturedUrl).toContain(`/catalogs/${CATALOG_ID}/items`);
    expect(capturedBody).toEqual({
      title: "Super Mario 64",
      cover_image_url: "https://example.com/sm64.jpg",
    });
  });

  it("returns the created item mapped to camelCase", async () => {
    server.use(
      http.post(`${API_URL}/catalogs/:id/items`, () =>
        HttpResponse.json(
          { ...mockCatalogItem, id: "cat-item-new", title: "Star Fox 64" },
          { status: 201 },
        ),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCreateCatalogItem(CATALOG_ID), {
      wrapper,
    });

    await act(async () => {
      result.current.mutate({ title: "Star Fox 64" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe("cat-item-new");
    expect(result.current.data?.title).toBe("Star Fox 64");
    expect(result.current.data?.catalogId).toBe(CATALOG_ID);
  });

  it("invalidates the catalog items query on success", async () => {
    server.use(
      http.post(`${API_URL}/catalogs/:id/items`, () =>
        HttpResponse.json(mockCatalogItem, { status: 201 }),
      ),
    );

    const { wrapper, queryClient } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCreateCatalogItem(CATALOG_ID), {
      wrapper,
    });

    await act(async () => {
      result.current.mutate({ title: "Banjo-Kazooie" });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["catalogs", CATALOG_ID, "items"],
    });
  });

  it("does not invalidate queries when the request fails", async () => {
    server.use(
      http.post(`${API_URL}/catalogs/:id/items`, () =>
        HttpResponse.json({ detail: "Not found" }, { status: 404 }),
      ),
    );

    const { wrapper, queryClient } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCreateCatalogItem(CATALOG_ID), {
      wrapper,
    });

    await act(async () => {
      result.current.mutate({ title: "Missing Catalog" });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
