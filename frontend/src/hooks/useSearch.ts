/**
 * Hook for searching catalog items.
 *
 * Uses debounced query to avoid excessive API calls and keeps
 * previous data while loading to prevent flickering.
 *
 * Requirements: 6.9
 */

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { searchApi } from "../services/searchApi";
import type {
  CatalogSearchFilters,
  CatalogSearchResult,
} from "../types/search";
import { useDebouncedValue } from "./useDebouncedValue";

const DEBOUNCE_DELAY_MS = 300;

/**
 * Hook for searching catalog items.
 *
 * @param filters - Search filters
 * @param skip - Number of results to skip (pagination)
 * @param limit - Maximum number of results
 * @returns Query result with debounced search
 */
export function useSearch(
  filters: CatalogSearchFilters = {},
  skip = 0,
  limit = 100,
) {
  // Debounce the search query
  const debouncedQuery = useDebouncedValue(filters.q, DEBOUNCE_DELAY_MS);

  // Build filters with debounced query
  const debouncedFilters: CatalogSearchFilters = {
    ...filters,
    q: debouncedQuery,
  };

  // Determine if we should search (only if there's a query or filters)
  const hasQuery = Boolean(debouncedQuery);
  const hasFilters = Object.entries(filters).some(([key, value]) => {
    if (key === "q") return false; // Already handled
    return value !== undefined && value !== null && value !== "";
  });

  return useQuery<CatalogSearchResult>({
    queryKey: ["search", "catalog-items", debouncedFilters, skip, limit],
    queryFn: () => searchApi.catalogItems(debouncedFilters, skip, limit),
    enabled: hasQuery || hasFilters,
    placeholderData: (previousData) => previousData,
  });
}

/**
 * Hook for managing search state with pagination.
 *
 * @param initialFilters - Initial search filters
 * @param pageSize - Number of results per page
 * @returns Search state and controls
 */
export function useSearchState(
  initialFilters: CatalogSearchFilters = {},
  pageSize = 20,
) {
  const [filters, setFilters] = useState<CatalogSearchFilters>(initialFilters);
  const [page, setPage] = useState(0);

  const updateFilters = (newFilters: Partial<CatalogSearchFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPage(0); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({});
    setPage(0);
  };

  const searchQuery = useSearch(filters, page * pageSize, pageSize);

  return {
    filters,
    updateFilters,
    clearFilters,
    page,
    setPage,
    pageSize,
    ...searchQuery,
  };
}
