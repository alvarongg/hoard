import { useTranslation } from "react-i18next";
import { EmptyState } from "../ui/EmptyState";
import type { LowStockEntry } from "../../types/accessory";

interface LowStockListProps {
  entries: LowStockEntry[];
}

export function LowStockList({ entries }: LowStockListProps) {
  const { t } = useTranslation();

  if (entries.length === 0) {
    return <EmptyState title={t("accessories.noLowStock")} />;
  }

  return (
    <section aria-labelledby="low-stock-heading">
      <h3
        id="low-stock-heading"
        className="mb-2 text-sm font-semibold text-gray-900 dark:text-white"
      >
        {t("accessories.lowStockTitle")}
      </h3>
      <ul className="space-y-1" role="list">
        {entries.map((e) => (
          <li key={e.id} className="flex items-center justify-between text-sm">
            <span className="text-gray-700 dark:text-gray-300">{e.name}</span>
            <span className="font-medium text-yellow-700 dark:text-yellow-400">
              {t("accessories.suggestedReorder", {
                available: e.quantityAvailable,
                reorder: e.reorderQuantity ?? "—",
              })}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
