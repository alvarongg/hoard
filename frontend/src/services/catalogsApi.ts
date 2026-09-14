import { fetchApi, toSnakeCase } from "./api";
import type {
  BatchImportResult,
  Catalog,
  CatalogCreate,
} from "../types/catalog";
import type { CatalogItem, CatalogItemCreate } from "../types/item";

export const catalogsApi = {
  list: (skip = 0, limit = 100): Promise<Catalog[]> =>
    fetchApi<Catalog[]>(`/catalogs?skip=${skip}&limit=${limit}`),

  getById: (id: string): Promise<Catalog> =>
    fetchApi<Catalog>(`/catalogs/${id}`),

  create: (data: CatalogCreate): Promise<Catalog> =>
    fetchApi<Catalog>("/catalogs", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  listItems: (catalogId: string, skip = 0, limit = 100): Promise<CatalogItem[]> =>
    fetchApi<CatalogItem[]>(
      `/catalogs/${catalogId}/items?skip=${skip}&limit=${limit}`,
    ),

  createItem: (
    catalogId: string,
    data: CatalogItemCreate,
  ): Promise<CatalogItem> =>
    fetchApi<CatalogItem>(`/catalogs/${catalogId}/items`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  importCsv: (catalogId: string, file: File): Promise<BatchImportResult> => {
    const formData = new FormData();
    formData.append("file", file);

    return fetchApi<BatchImportResult>(`/catalogs/${catalogId}/import-csv`, {
      method: "POST",
      body: formData,
    });
  },

  searchItems: (query: string): Promise<CatalogItem[]> =>
    fetchApi<CatalogItem[]>(
      `/catalog-items/search?q=${encodeURIComponent(query)}`,
    ),
};
