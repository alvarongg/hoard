import { describe, it, expect, vi, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { mockCatalogItem } from "../test/mocks/handlers";
import { catalogsApi } from "./catalogsApi";
import { ApiError } from "./api";

const API_URL = "http://localhost:8000/api";

interface CapturedRequest {
  url: string;
  method: string;
  body: Record<string, unknown>;
}

function captureCreateItem(
  captured: CapturedRequest,
  status = 201,
  responseBody: Record<string, unknown> | null = null,
): void {
  server.use(
    http.post(`${API_URL}/catalogs/:catalogId/items`, async ({ request }) => {
      captured.url = request.url;
      captured.method = request.method;
      captured.body = (await request.json()) as Record<string, unknown>;

      if (status >= 400) {
        return HttpResponse.json({ detail: "Catalog not found" }, { status });
      }

      return HttpResponse.json(
        responseBody ?? { ...mockCatalogItem, ...captured.body },
        { status },
      );
    }),
  );
}

function newCapture(): CapturedRequest {
  return { url: "", method: "", body: {} };
}

describe("catalogsApi", () => {
  describe("createItem", () => {
    it("sends POST to the catalog items endpoint", async () => {
      const captured = newCapture();
      captureCreateItem(captured);

      await catalogsApi.createItem("catalog-1", { title: "Super Mario 64" });

      expect(captured.method).toBe("POST");
      expect(captured.url).toBe(`${API_URL}/catalogs/catalog-1/items`);
    });

    it("converts camelCase body keys to snake_case", async () => {
      const captured = newCapture();
      captureCreateItem(captured);

      await catalogsApi.createItem("catalog-1", {
        title: "Super Mario 64",
        subtitle: "Shindou Edition",
        coverImageUrl: "https://example.com/cover.jpg",
        customFields: { serialNumber: "NUS-001" },
      });

      expect(captured.body).toEqual({
        title: "Super Mario 64",
        subtitle: "Shindou Edition",
        cover_image_url: "https://example.com/cover.jpg",
        custom_fields: { serial_number: "NUS-001" },
      });
      expect(captured.body).not.toHaveProperty("coverImageUrl");
    });

    it("sends only the provided fields in the body", async () => {
      const captured = newCapture();
      captureCreateItem(captured);

      await catalogsApi.createItem("catalog-1", { title: "GoldenEye 007" });

      expect(Object.keys(captured.body)).toEqual(["title"]);
    });

    it("encodes the catalogId into the URL path", async () => {
      const captured = newCapture();
      captureCreateItem(captured);

      await catalogsApi.createItem("catalog-99", { title: "Banjo-Kazooie" });

      expect(captured.url).toContain("/catalogs/catalog-99/items");
    });

    it("returns the created item with camelCase keys", async () => {
      const captured = newCapture();
      captureCreateItem(captured);

      const result = await catalogsApi.createItem("catalog-1", {
        title: "Super Mario 64",
      });

      expect(result.id).toBe(mockCatalogItem.id);
      expect(result.title).toBe("Super Mario 64");
      expect(result).toHaveProperty("catalogId", "catalog-1");
      expect(result).toHaveProperty("coverImageUrl");
      expect(result).not.toHaveProperty("catalog_id");
    });

    it("throws ApiError when the catalog does not exist", async () => {
      const captured = newCapture();
      captureCreateItem(captured, 404);

      await expect(
        catalogsApi.createItem("missing", { title: "Conker" }),
      ).rejects.toThrow(ApiError);
    });
  });
});

describe("catalogsApi.importCsv", () => {
  interface CapturedUpload {
    url: string;
    method: string;
    contentType: string | null;
    formData: FormData | null;
  }

  function newUploadCapture(): CapturedUpload {
    return { url: "", method: "", contentType: null, formData: null };
  }

  /**
   * The request body is captured at the fetch layer: reading a multipart body
   * back from the intercepted request is not supported in this environment.
   */
  function captureFetch(captured: CapturedUpload): void {
    const originalFetch = globalThis.fetch.bind(globalThis);

    vi.spyOn(globalThis, "fetch").mockImplementation(
      (input: RequestInfo | URL, init?: RequestInit) => {
        captured.url = typeof input === "string" ? input : String(input);
        captured.method = init?.method ?? "GET";
        const headers = (init?.headers ?? {}) as Record<string, string>;
        captured.contentType = headers["Content-Type"] ?? null;
        captured.formData =
          init?.body instanceof FormData ? init.body : null;
        return originalFetch(input, init);
      },
    );
  }

  function mockImportCsv(
    status = 200,
    responseBody: Record<string, unknown> = {
      created_count: 0,
      error_count: 0,
      errors: [],
    },
  ): void {
    server.use(
      http.post(`${API_URL}/catalogs/:catalogId/import-csv`, () => {
        if (status >= 400) {
          return HttpResponse.json({ detail: "Catalog not found" }, { status });
        }
        return HttpResponse.json(responseBody, { status });
      }),
    );
  }

  function csvFile(
    name = "items.csv",
    content = "title\nSuper Mario 64\n",
  ): File {
    return new File([content], name, { type: "text/csv" });
  }

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends POST to the import-csv endpoint", async () => {
    const captured = newUploadCapture();
    captureFetch(captured);
    mockImportCsv();

    await catalogsApi.importCsv("catalog-1", csvFile());

    expect(captured.method).toBe("POST");
    expect(captured.url).toContain("/catalogs/catalog-1/import-csv");
  });

  it("sends the file as FormData under the 'file' field", async () => {
    const captured = newUploadCapture();
    captureFetch(captured);
    mockImportCsv();

    await catalogsApi.importCsv("catalog-1", csvFile("catalog.csv"));

    const sentFile = captured.formData?.get("file");
    expect(sentFile).toBeInstanceOf(File);
    expect((sentFile as File).name).toBe("catalog.csv");
  });

  it("does not set a Content-Type header so the browser adds the boundary", async () => {
    const captured = newUploadCapture();
    captureFetch(captured);
    mockImportCsv();

    await catalogsApi.importCsv("catalog-1", csvFile());

    expect(captured.contentType).toBeNull();
  });

  it("returns the result converted to camelCase", async () => {
    mockImportCsv(200, {
      created_count: 2,
      error_count: 1,
      errors: [{ row: 3, message: "Missing title" }],
    });

    const result = await catalogsApi.importCsv("catalog-1", csvFile());

    expect(result).toEqual({
      createdCount: 2,
      errorCount: 1,
      errors: [{ row: 3, message: "Missing title" }],
    });
    expect(result).not.toHaveProperty("created_count");
  });

  it("returns an empty error list when the import has no errors", async () => {
    mockImportCsv(200, { created_count: 5, error_count: 0, errors: [] });

    const result = await catalogsApi.importCsv("catalog-1", csvFile());

    expect(result.createdCount).toBe(5);
    expect(result.errors).toEqual([]);
  });

  it("throws ApiError when the catalog does not exist", async () => {
    mockImportCsv(404);

    await expect(catalogsApi.importCsv("missing", csvFile())).rejects.toThrow(
      ApiError,
    );
  });
});
