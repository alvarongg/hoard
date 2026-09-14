import { useTranslation } from "react-i18next";
import type { CollectionItem, ItemCondition } from "../../types/item";

interface ItemCardProps {
  item: CollectionItem;
  catalogTitle?: string;
  catalogName?: string;
  primaryImageUrl?: string;
  onEdit?: (id: string) => void;
}

const CONDITION_KEYS: Record<ItemCondition, string> = {
  mint: "items.mint",
  near_mint: "items.nearMint",
  excellent: "items.excellent",
  good: "items.good",
  fair: "items.fair",
  poor: "items.poor",
};

export function ItemCard({
  item,
  catalogTitle,
  catalogName,
  primaryImageUrl,
  onEdit,
}: ItemCardProps) {
  const { t } = useTranslation();
  const headingId = `item-${item.id}`;

  return (
    <article
      aria-labelledby={headingId}
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      {primaryImageUrl && (
        <img
          src={primaryImageUrl}
          alt=""
          className="mb-3 h-40 w-full rounded-md object-cover"
          loading="lazy"
        />
      )}
      <h3 id={headingId} className="text-base font-semibold text-gray-900">
        {catalogTitle ?? item.catalogItemId}
      </h3>
      {catalogName && (
        <p className="text-xs text-gray-400">{catalogName}</p>
      )}
      <p className="mt-1 text-sm text-gray-500">
        {t("items.condition")}: {t(CONDITION_KEYS[item.condition])}
      </p>
      {item.purchasePrice !== null && (
        <p className="mt-1 text-sm text-gray-600">
          {t("items.price")}: {item.purchaseCurrency} {item.purchasePrice}
        </p>
      )}
      {onEdit && (
        <button
          onClick={() => onEdit(item.id)}
          aria-label={t("items.edit")}
          className="mt-2 rounded-md bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {t("common.edit")}
        </button>
      )}
    </article>
  );
}
