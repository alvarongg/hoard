import { useTranslation } from "react-i18next";
import type { LatestPriceEntry } from "../../types/priceHistory";

interface LatestPriceSummaryProps {
  entries: LatestPriceEntry[];
}

/**
 * LatestPriceSummary - shows the most recent price per condition.
 */
export function LatestPriceSummary({ entries }: LatestPriceSummaryProps) {
  const { t } = useTranslation();

  if (entries.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400">
        {t("priceHistory.empty")}
      </p>
    );
  }

  return (
    <section aria-labelledby="latest-price-heading">
      <h3
        id="latest-price-heading"
        className="mb-2 text-sm font-semibold text-gray-900 dark:text-white"
      >
        {t("priceHistory.latest")}
      </h3>
      <ul className="space-y-1" role="list">
        {entries.map((entry) => (
          <li
            key={`${entry.condition}-${entry.isComplete}`}
            className="flex items-center justify-between text-sm"
          >
            <span className="text-gray-700 dark:text-gray-300">
              {entry.condition}
              {!entry.isComplete && (
                <span className="ml-1 text-xs text-gray-500">
                  ({t("priceHistory.incompleteShort")})
                </span>
              )}
            </span>
            <span className="font-medium text-gray-900 dark:text-white">
              {entry.price} {entry.currency}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
