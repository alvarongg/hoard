/**
 * Collection stats panel component.
 *
 * Displays statistics for a collection including total items, investment,
 * value, ROI, and item counts.
 */

import { useTranslation } from "react-i18next";
import type { CollectionStats } from "../../types/collection";

interface CollectionStatsPanelProps {
  stats: CollectionStats;
}

export function CollectionStatsPanel({ stats }: CollectionStatsPanelProps) {
  const { t } = useTranslation();

  const formatCurrency = (value: number | null): string => {
    if (value === null) return "—";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatPercentage = (value: number | null): string => {
    if (value === null) return t("collections.stats.roiUnavailable");
    return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`;
  };

  return (
    <section
      aria-labelledby="collection-stats-heading"
      className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
    >
      <h3
        id="collection-stats-heading"
        className="mb-4 text-lg font-semibold text-gray-900 dark:text-white"
      >
        {t("collections.stats.title")}
      </h3>

      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.totalItems")}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.totalItems}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.differentCategories")}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.differentCategoriesCount}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.totalInvested")}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {formatCurrency(stats.totalInvested)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.currentValue")}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {formatCurrency(stats.currentValue)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.valueGain")}
          </dt>
          <dd
            className={`mt-1 text-2xl font-semibold ${
              stats.valueGain === null
                ? "text-gray-900 dark:text-white"
                : stats.valueGain >= 0
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
            }`}
          >
            {formatCurrency(stats.valueGain)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.roi")}
          </dt>
          <dd
            className={`mt-1 text-2xl font-semibold ${
              stats.roiPercentage === null
                ? "text-gray-500 dark:text-gray-400"
                : stats.roiPercentage >= 0
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
            }`}
          >
            {formatPercentage(stats.roiPercentage)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.completeItems")}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.completeItems}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t("collections.stats.gradedItems")}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.gradedItems}
          </dd>
        </div>
      </dl>
    </section>
  );
}
