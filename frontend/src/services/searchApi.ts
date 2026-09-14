/**
 * API client for catalog search.
 *
 * Requirements: 6.5, 6.8, 19.7
 */

import { fetchApi, toSnakeCase } from "./api";
import type {
  CatalogSearchFilters,
  CatalogSearchResult,
} from "../types/search";

/**
 * Build query string from filters, omitting undefined values.
 */
function buildQueryString(
  filters: CatalogSearchFilters,
  skip: number,
  limit: number,
): string {
  const params = new URLSearchParams();

  // Add pagination
  params.set("skip", String(skip));
  params.set("limit", String(limit));

  // Add filters (only defined values)
  const snakeFilters = toSnakeCase<Record<string, unknown>>(filters);
  for (const [key, value] of Object.entries(snakeFilters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }

  return params.toString();
}

export const searchApi = {
  /**
   * Search catalog items with filters and pagination.
   */
  catalogItems: (
    filters: CatalogSearchFilters = {},
    skip = 0,
    limit = 100,
  ): Promise<CatalogSearchResult> => {
    const queryString = buildQueryString(filters, skip, limit);
    return fetchApi<CatalogSearchResult>(`/search/catalog-items?${queryString}`);
  },
};
