import { fetchApi, toSnakeCase } from "./api";
import type { Catalog, CatalogCreate } from "../types/catalog";
import type { CatalogItem } from "../types/item";

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

  searchItems: (query: string): Promise<CatalogItem[]> =>
    fetchApi<CatalogItem[]>(
      `/catalog-items/search?q=${encodeURIComponent(query)}`,
    ),
};
