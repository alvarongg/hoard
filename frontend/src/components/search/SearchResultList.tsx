/**
 * SearchResultList component for displaying search results.
 *
 * Requirements: 6.7, 6.10
 */

import { useTranslation } from "react-i18next";
import type { CatalogSearchResultItem } from "../../types/search";

interface SearchResultListProps {
  /** Search result items */
  items: CatalogSearchResultItem[];
  /** Callback when an item is selected */
  onSelect?: (item: CatalogSearchResultItem) => void;
  /** Whether results are loading */
  isLoading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
}

/**
 * Accessible list of search results.
 */
export function SearchResultList({
  items,
  onSelect,
  isLoading = false,
  emptyMessage,
}: SearchResultListProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center justify-center py-12"
      >
        <svg
          className="h-8 w-8 animate-spin text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span className="ml-2 text-gray-500">{t("common.loading")}</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="py-12 text-center text-gray-500"
      >
        <p>{emptyMessage ?? t("search.noResults")}</p>
        <p className="mt-2 text-sm">{t("search.noResultsHint")}</p>
      </div>
    );
  }

  return (
    <ul
      role="listbox"
      aria-label={t("search.resultsLabel")}
      className="divide-y divide-gray-200 dark:divide-gray-700"
    >
      {items.map((item) => (
        <li key={item.id} role="presentation">
          <button
            type="button"
            role="option"
            onClick={() => onSelect?.(item)}
            className="w-full cursor-pointer border-none bg-transparent px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 dark:hover:bg-gray-800 dark:focus:bg-gray-800"
          >
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-gray-900 dark:text-white">
                  {item.title}
                </p>
                {item.subtitle && (
                  <p className="mt-1 truncate text-sm text-gray-500 dark:text-gray-400">
                    {item.subtitle}
                  </p>
                )}
              </div>
              <span className="ml-3 shrink-0 text-xs text-gray-400 dark:text-gray-500">
                {item.catalogId}
              </span>
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
