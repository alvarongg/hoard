import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCsvImport } from "./useCsvImport";

const API_URL = "http://localhost:8000/api";
const CATALOG_ID = "catalog-1";

function csvFile(name = "items.csv", content = "title\nSuper Mario 64\n"): File {
  return new File([content], name, { type: "text/csv" });
}

describe("useCsvImport", () => {
  it("uploads the file to the import-csv endpoint as multipart form data", async () => {
    let capturedUrl = "";
    let capturedMethod = "";
    let capturedContentType: string | null = "";

    server.use(
      http.post(`${API_URL}/catalogs/:id/import-csv`, ({ request }) => {
        capturedUrl = request.url;
        capturedMethod = request.method;
        capturedContentType = request.headers.get("Content-Type");
        return HttpResponse.json({
          created_count: 1,
          error_count: 0,
          errors: [],
        });
      }),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCsvImport(CATALOG_ID), { wrapper });

    await act(async () => {
      result.current.mutate(csvFile("catalog.csv"));
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(capturedMethod).toBe("POST");
    expect(capturedUrl).toContain(`/catalogs/${CATALOG_ID}/import-csv`);
    expect(capturedContentType).toContain("multipart/form-data");
  });

  it("exposes the import result in camelCase", async () => {
    server.use(
      http.post(`${API_URL}/catalogs/:id/import-csv`, () =>
        HttpResponse.json({
          created_count: 3,
          error_count: 2,
          errors: [
            { row: 2, message: "Missing title" },
            { row: 5, message: "Title too long" },
          ],
        }),
      ),
    );

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useCsvImport(CATALOG_ID), { wrapper });

    await act(async () => {
      result.current.mutate(csvFile());
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({
      createdCount: 3,
      errorCount: 2,
      errors: [
        { row: 2, message: "Missing title" },
        { row: 5, message: "Title too long" },
      ],
    });
  });

  it("invalidates the catalog item and catalog queries on success", async () => {
    server.use(
      http.post(`${API_URL}/catalogs/:id/import-csv`, () =>
        HttpResponse.json({ created_count: 1, error_count: 0, errors: [] }),
      ),
    );

    const { wrapper, queryClient } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCsvImport(CATALOG_ID), { wrapper });

    await act(async () => {
      result.current.mutate(csvFile());
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ["catalogs", CATALOG_ID, "items"],
    });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["catalogs"] });
  });

  it("does not invalidate queries when the import fails", async () => {
    server.use(
      http.post(`${API_URL}/catalogs/:id/import-csv`, () =>
        HttpResponse.json({ detail: "Catalog not found" }, { status: 404 }),
      ),
    );

    const { wrapper, queryClient } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCsvImport(CATALOG_ID), { wrapper });

    await act(async () => {
      result.current.mutate(csvFile());
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
