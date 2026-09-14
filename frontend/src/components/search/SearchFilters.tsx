/**
 * SearchFilters component for catalog search.
 *
 * Provides accessible filter controls for refining search results.
 *
 * Requirements: 6.4, 6.7, 6.10
 */

import { useTranslation } from "react-i18next";
import type { CatalogSearchFilters } from "../../types/search";

interface SearchFiltersProps {
  /** Current filter values */
  filters: CatalogSearchFilters;
  /** Callback when filters change */
  onFiltersChange: (filters: CatalogSearchFilters) => void;
  /** Available filter options */
  options?: {
    mainCategories?: Array<{ id: string; name: string }>;
    subCategories?: Array<{ id: string; name: string }>;
    languages?: string[];
    regions?: string[];
    rarities?: string[];
  };
}

/**
 * Accessible filter controls for search.
 */
export function SearchFilters({
  filters,
  onFiltersChange,
  options,
}: SearchFiltersProps) {
  const { t } = useTranslation();

  const handleFilterChange = (
    key: keyof CatalogSearchFilters,
    value: string | undefined,
  ) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const handleYearChange = (
    key: "yearMin" | "yearMax",
    value: string,
  ) => {
    const numValue = value ? parseInt(value, 10) : undefined;
    onFiltersChange({
      ...filters,
      [key]: numValue,
    });
  };

  const hasActiveFilters = Object.entries(filters).some(([key, value]) => {
    if (key === "q") return false; // Query is not a filter
    return value !== undefined && value !== null && value !== "";
  });

  const clearFilters = () => {
    const cleared: CatalogSearchFilters = { q: filters.q };
    onFiltersChange(cleared);
  };

  return (
    <section aria-labelledby="filters-heading" className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 id="filters-heading" className="text-lg font-medium">
          {t("search.filters.title")}
        </h2>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="text-sm text-primary-600 hover:text-primary-700 focus:outline-none focus:underline dark:text-primary-400"
          >
            {t("common.clearFilters")}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Main Category Filter */}
        {options?.mainCategories && (
          <div>
            <label
              htmlFor="filter-main-category"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t("search.filters.mainCategory")}
            </label>
            <select
              id="filter-main-category"
              value={filters.mainCategoryId ?? ""}
              onChange={(e) =>
                handleFilterChange("mainCategoryId", e.target.value)
              }
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">{t("common.all")}</option>
              {options.mainCategories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Sub Category Filter */}
        {options?.subCategories && (
          <div>
            <label
              htmlFor="filter-sub-category"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t("search.filters.subCategory")}
            </label>
            <select
              id="filter-sub-category"
              value={filters.subCategoryId ?? ""}
              onChange={(e) =>
                handleFilterChange("subCategoryId", e.target.value)
              }
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">{t("common.all")}</option>
              {options.subCategories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Language Filter */}
        {options?.languages && (
          <div>
            <label
              htmlFor="filter-language"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t("search.filters.language")}
            </label>
            <select
              id="filter-language"
              value={filters.language ?? ""}
              onChange={(e) => handleFilterChange("language", e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">{t("common.all")}</option>
              {options.languages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Region Filter */}
        {options?.regions && (
          <div>
            <label
              htmlFor="filter-region"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t("search.filters.region")}
            </label>
            <select
              id="filter-region"
              value={filters.region ?? ""}
              onChange={(e) => handleFilterChange("region", e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">{t("common.all")}</option>
              {options.regions.map((reg) => (
                <option key={reg} value={reg}>
                  {reg}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Rarity Filter */}
        {options?.rarities && (
          <div>
            <label
              htmlFor="filter-rarity"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t("search.filters.rarity")}
            </label>
            <select
              id="filter-rarity"
              value={filters.rarity ?? ""}
              onChange={(e) => handleFilterChange("rarity", e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">{t("common.all")}</option>
              {options.rarities.map((rar) => (
                <option key={rar} value={rar}>
                  {rar}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Year Range */}
        <div>
          <label
            htmlFor="filter-year-min"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {t("search.filters.yearMin")}
          </label>
          <input
            id="filter-year-min"
            type="number"
            min={1800}
            max={2200}
            value={filters.yearMin ?? ""}
            onChange={(e) => handleYearChange("yearMin", e.target.value)}
            placeholder="1800"
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </div>

        <div>
          <label
            htmlFor="filter-year-max"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {t("search.filters.yearMax")}
          </label>
          <input
            id="filter-year-max"
            type="number"
            min={1800}
            max={2200}
            value={filters.yearMax ?? ""}
            onChange={(e) => handleYearChange("yearMax", e.target.value)}
            placeholder={String(new Date().getFullYear())}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </div>

        {/* Text Filters */}
        <div>
          <label
            htmlFor="filter-manufacturer"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {t("search.filters.manufacturer")}
          </label>
          <input
            id="filter-manufacturer"
            type="text"
            value={filters.manufacturer ?? ""}
            onChange={(e) =>
              handleFilterChange("manufacturer", e.target.value)
            }
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </div>

        <div>
          <label
            htmlFor="filter-publisher"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {t("search.filters.publisher")}
          </label>
          <input
            id="filter-publisher"
            type="text"
            value={filters.publisher ?? ""}
            onChange={(e) => handleFilterChange("publisher", e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </div>

        <div>
          <label
            htmlFor="filter-developer"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {t("search.filters.developer")}
          </label>
          <input
            id="filter-developer"
            type="text"
            value={filters.developer ?? ""}
            onChange={(e) => handleFilterChange("developer", e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </div>

        <div>
          <label
            htmlFor="filter-brand"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {t("search.filters.brand")}
          </label>
          <input
            id="filter-brand"
            type="text"
            value={filters.brand ?? ""}
            onChange={(e) => handleFilterChange("brand", e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </div>
      </div>
    </section>
  );
}
