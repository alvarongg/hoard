/**
 * SearchBar component for catalog search.
 *
 * Provides an accessible search input with loading indicator and result count.
 *
 * Requirements: 6.4, 6.9, 6.10
 */

import { useTranslation } from "react-i18next";

interface SearchBarProps {
  /** Current search value */
  value: string;
  /** Callback when value changes */
  onChange: (value: string) => void;
  /** Total number of results (for announcement) */
  resultCount?: number;
  /** Whether a search is in progress */
  isLoading?: boolean;
  /** Placeholder text */
  placeholder?: string;
}

/**
 * Accessible search bar with loading indicator and result count announcement.
 */
export function SearchBar({
  value,
  onChange,
  resultCount,
  isLoading = false,
  placeholder,
}: SearchBarProps) {
  const { t } = useTranslation();

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <label htmlFor="search-input" className="sr-only">
          {t("search.placeholder")}
        </label>
        <div className="relative flex-1">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </span>
          <input
            id="search-input"
            type="search"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder ?? t("search.placeholder")}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-10 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            aria-describedby="search-description"
          />
          {isLoading && (
            <span className="absolute inset-y-0 right-0 flex items-center pr-3">
              <svg
                className="h-5 w-5 animate-spin text-gray-400"
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
            </span>
          )}
        </div>
        {value && (
          <button
            type="button"
            onClick={() => onChange("")}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            aria-label={t("search.clearSearch")}
          >
            {t("common.clearFilters")}
          </button>
        )}
      </div>
      <span id="search-description" className="sr-only">
        {resultCount !== undefined
          ? t("search.resultCount", { count: resultCount })
          : t("search.searchHint")}
      </span>
    </div>
  );
}
