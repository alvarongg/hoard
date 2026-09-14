import { useTranslation } from "react-i18next";
import type { Urgency } from "../../types/wishlist";

interface WishlistFiltersProps {
  priority: number | undefined;
  urgency: Urgency | undefined;
  isActive: boolean | undefined;
  includeAcquired: boolean;
  onPriorityChange: (priority: number | undefined) => void;
  onUrgencyChange: (urgency: Urgency | undefined) => void;
  onIsActiveChange: (isActive: boolean | undefined) => void;
  onIncludeAcquiredChange: (includeAcquired: boolean) => void;
  onClear: () => void;
}

/**
 * WishlistFilters - Filter component for wishlist items.
 *
 * Features:
 * - Filter by priority and urgency
 * - Toggle active items
 * - Toggle acquired items
 */
export function WishlistFilters({
  priority,
  urgency,
  isActive,
  includeAcquired,
  onPriorityChange,
  onUrgencyChange,
  onIsActiveChange,
  onIncludeAcquiredChange,
  onClear,
}: WishlistFiltersProps) {
  const { t } = useTranslation();

  const hasFilters = priority !== undefined || urgency !== undefined || isActive !== undefined || includeAcquired;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label htmlFor="filter-priority" className="block text-sm font-medium text-gray-700">
            {t("wishlist.filters.priority")}
          </label>
          <select
            id="filter-priority"
            value={priority ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              onPriorityChange(value ? parseInt(value, 10) : undefined);
            }}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">{t("common.all")}</option>
            <option value="1">{t("wishlist.priority.critical")}</option>
            <option value="2">{t("wishlist.priority.high")}</option>
            <option value="3">{t("wishlist.priority.medium")}</option>
            <option value="4">{t("wishlist.priority.low")}</option>
            <option value="5">{t("wishlist.priority.lowest")}</option>
          </select>
        </div>

        <div>
          <label htmlFor="filter-urgency" className="block text-sm font-medium text-gray-700">
            {t("wishlist.filters.urgency")}
          </label>
          <select
            id="filter-urgency"
            value={urgency ?? ""}
            onChange={(e) => {
              const value = e.target.value as Urgency | "";
              onUrgencyChange(value || undefined);
            }}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">{t("common.all")}</option>
            <option value="critical">{t("wishlist.urgency.critical")}</option>
            <option value="high">{t("wishlist.urgency.high")}</option>
            <option value="medium">{t("wishlist.urgency.medium")}</option>
            <option value="low">{t("wishlist.urgency.low")}</option>
          </select>
        </div>

        <div>
          <label htmlFor="filter-active" className="block text-sm font-medium text-gray-700">
            {t("wishlist.filters.status")}
          </label>
          <select
            id="filter-active"
            value={isActive === undefined ? "" : isActive ? "true" : "false"}
            onChange={(e) => {
              const value = e.target.value;
              onIsActiveChange(value === "" ? undefined : value === "true");
            }}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">{t("common.all")}</option>
            <option value="true">{t("wishlist.filters.activeOnly")}</option>
            <option value="false">{t("wishlist.filters.inactiveOnly")}</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="filter-acquired"
            checked={includeAcquired}
            onChange={(e) => onIncludeAcquiredChange(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="filter-acquired" className="text-sm font-medium text-gray-700">
            {t("wishlist.filters.includeAcquired")}
          </label>
        </div>

        {hasFilters && (
          <button
            type="button"
            onClick={onClear}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {t("common.clearFilters")}
          </button>
        )}
      </div>
    </div>
  );
}
