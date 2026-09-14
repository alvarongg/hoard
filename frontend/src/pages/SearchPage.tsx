/**
 * SearchPage component for catalog search.
 *
 * Requirements: 6.7, 6.8, 6.10
 */

import { useTranslation } from "react-i18next";
import { LiveRegion } from "../components/ui/LiveRegion";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { SearchBar } from "../components/search/SearchBar";
import { SearchFilters } from "../components/search/SearchFilters";
import { SearchResultList } from "../components/search/SearchResultList";
import { SearchModeNotice } from "../components/search/SearchModeNotice";
import { useSearchState } from "../hooks/useSearch";
import type { CatalogSearchResultItem } from "../types/search";

const PAGE_SIZE = 20;

export function SearchPage() {
  const { t } = useTranslation();
  const {
    filters,
    updateFilters,
    clearFilters,
    page,
    setPage,
    data,
    isLoading,
    isError,
    refetch,
  } = useSearchState({}, PAGE_SIZE);

  // Handle search query change
  const handleQueryChange = (q: string) => {
    updateFilters({ q });
  };

  // Handle item selection
  const handleItemSelect = (item: CatalogSearchResultItem) => {
    // Navigate to catalog item detail
    window.location.href = `/catalogs/${item.catalogId}/items/${item.id}`;
  };

  const resultCount = data?.total ?? 0;
  const searchMode = data?.searchMode ?? "degraded";

  // Derive the screen-reader announcement from current state (no effect needed):
  // once results settle, announce the count or the empty-state message.
  const announcement =
    !isLoading && data
      ? data.total === 0
        ? t("search.noResults")
        : t("search.resultCount", { count: data.total })
      : null;

  const handleClearFilters = () => {
    clearFilters();
  };

  if (isError) {
    return (
      <main>
        <ErrorMessage
          message={t("errors.searchFailed")}
          onRetry={() => refetch()}
        />
      </main>
    );
  }

  return (
    <main>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("search.title")}
      </h1>

      {/* Search bar */}
      <div className="mt-4">
        <SearchBar
          value={filters.q ?? ""}
          onChange={handleQueryChange}
          resultCount={resultCount}
          isLoading={isLoading}
        />
      </div>

      {/* Search mode notice */}
      {searchMode === "degraded" && (
        <div className="mt-4">
          <SearchModeNotice mode={searchMode} />
        </div>
      )}

      {/* Filters */}
      <div className="mt-6">
        <SearchFilters
          filters={filters}
          onFiltersChange={updateFilters}
        />
        <button
          type="button"
          onClick={handleClearFilters}
          className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded dark:text-blue-400"
        >
          {t("search.clearFilters")}
        </button>
      </div>

      {/* Results */}
      <section aria-labelledby="results-heading" className="mt-6">
        <h2 id="results-heading" className="sr-only">
          {t("search.results")}
        </h2>

        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <>
            <SearchResultList
              items={data?.items ?? []}
              onSelect={handleItemSelect}
              emptyMessage={
                filters.q || Object.keys(filters).length > 1
                  ? t("search.noResults")
                  : t("search.enterQuery")
              }
            />

            {/* Pagination */}
            {resultCount > PAGE_SIZE && (
              <nav
                aria-label={t("search.pagination")}
                className="mt-6 flex items-center justify-between"
              >
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  {t("common.previous")}
                </button>

                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {t("search.pageStatus", {
                    current: page + 1,
                    total: Math.ceil(resultCount / PAGE_SIZE),
                  })}
                </span>

                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={(page + 1) * PAGE_SIZE >= resultCount}
                  className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  {t("common.next")}
                </button>
              </nav>
            )}
          </>
        )}
      </section>

      {/* Live region for announcements */}
      {announcement && <LiveRegion message={announcement} />}
    </main>
  );
}
