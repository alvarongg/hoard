import { useTranslation } from "react-i18next";
import type { PriceAggregates } from "../../types/wishlist";

interface PriceAggregatesPanelProps {
  aggregates: PriceAggregates;
  currency?: string;
}

/**
 * PriceAggregatesPanel - Panel component for displaying price statistics.
 *
 * Shows average, min, max prices and sighting counts.
 */
export function PriceAggregatesPanel({ aggregates, currency = "USD" }: PriceAggregatesPanelProps) {
  const { t } = useTranslation();

  const formatPrice = (price: number | null) => {
    if (price === null) return t("wishlist.aggregates.noData");
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(price);
  };

  return (
    <section aria-labelledby="price-aggregates-heading" className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 id="price-aggregates-heading" className="text-lg font-semibold text-gray-900">
        {t("wishlist.aggregates.title")}
      </h3>

      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-sm font-medium text-gray-500">{t("wishlist.aggregates.average")}</dt>
          <dd className="mt-1 text-lg font-semibold text-gray-900">
            {formatPrice(aggregates.avgPrice)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500">{t("wishlist.aggregates.minimum")}</dt>
          <dd className="mt-1 text-lg font-semibold text-green-600">
            {formatPrice(aggregates.minPrice)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500">{t("wishlist.aggregates.maximum")}</dt>
          <dd className="mt-1 text-lg font-semibold text-red-600">
            {formatPrice(aggregates.maxPrice)}
          </dd>
        </div>

        <div>
          <dt className="text-sm font-medium text-gray-500">{t("wishlist.aggregates.totalSightings")}</dt>
          <dd className="mt-1 text-lg font-semibold text-gray-900">
            {aggregates.totalSightings}
          </dd>
        </div>
      </dl>

      {aggregates.totalSightings > 0 && (
        <p className="mt-3 text-sm text-gray-500">
          {t("wishlist.aggregates.availableCount", { count: aggregates.availableSightings })}
        </p>
      )}
    </section>
  );
}
