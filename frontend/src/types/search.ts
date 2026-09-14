/**
 * Types for advanced catalog search.
 *
 * Requirements: 6.5, 6.8, 19.7
 */

/**
 * Search mode used for the query.
 */
export type SearchMode = "full_text" | "fuzzy" | "degraded";

/**
 * Filters for catalog item search.
 */
export interface CatalogSearchFilters {
  q?: string;
  mainCategoryId?: string;
  subCategoryId?: string;
  language?: string;
  region?: string;
  manufacturer?: string;
  publisher?: string;
  developer?: string;
  brand?: string;
  rarity?: string;
  yearMin?: number;
  yearMax?: number;
}

/**
 * A single catalog item in search results.
 */
export interface CatalogSearchResultItem {
  id: string;
  title: string;
  subtitle: string | null;
  catalogId: string;
}

/**
 * Result of a catalog search.
 */
export interface CatalogSearchResult {
  items: CatalogSearchResultItem[];
  total: number;
  searchMode: SearchMode;
}
