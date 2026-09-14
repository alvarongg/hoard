import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { WishlistItem } from "../../types/wishlist";
import { Badge } from "../ui/Badge";
import { PriorityBadge } from "./PriorityBadge";
import { UrgencyBadge } from "./UrgencyBadge";

interface WishlistCardProps {
  item: WishlistItem;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

/**
 * WishlistCard - Card component for displaying a wishlist item.
 *
 * Features:
 * - Displays priority and urgency badges
 * - Shows budget, condition, and notes
 * - Edit, delete, and view details actions
 * - Acquired status indicator
 */
export function WishlistCard({ item, onEdit, onDelete, onView }: WishlistCardProps) {
  const { t } = useTranslation();
  const headingId = `wishlist-item-${item.id}`;

  const formatPrice = (price: number | null, currency: string) => {
    if (price === null) return null;
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(price);
  };

  return (
    <article
      aria-labelledby={headingId}
      className={`rounded-lg border p-4 shadow-sm ${
        item.isAcquired
          ? "border-green-200 bg-green-50"
          : "border-gray-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 id={headingId} className="text-lg font-semibold text-gray-900">
              {t("wishlist.itemTitle", { id: item.id.slice(0, 8) })}
            </h2>
            {item.isAcquired && (
              <Badge label={t("wishlist.acquired")} tone="success" />
            )}
          </div>

          <div className="mt-2 flex flex-wrap gap-2">
            <PriorityBadge priority={item.priority} />
            <UrgencyBadge urgency={item.urgency} />
            {!item.isActive && (
              <Badge label={t("wishlist.inactive")} tone="neutral" />
            )}
          </div>
        </div>
      </div>

      <div className="mt-3 space-y-1 text-sm text-gray-600">
        {item.maxPrice !== null && (
          <p>
            <span className="font-medium">{t("wishlist.budget")}:</span>{" "}
            {formatPrice(item.maxPrice, item.currency)}
          </p>
        )}

        {item.desiredCondition && (
          <p>
            <span className="font-medium">{t("wishlist.condition")}:</span>{" "}
            {item.desiredCondition}
          </p>
        )}

        {item.mustBeComplete && (
          <p className="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 text-green-600" aria-hidden="true" focusable="false">
              <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
            </svg>
            <span>{t("wishlist.mustBeComplete")}</span>
          </p>
        )}

        {item.notes && (
          <p className="mt-2 italic text-gray-500 line-clamp-2">
            {item.notes}
          </p>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <Link
          to={`/wishlist/${item.id}`}
          onClick={() => onView(item.id)}
          className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
          aria-label={t("wishlist.viewDetails")}
        >
          {t("common.view")}
        </Link>
        <button
          onClick={() => onEdit(item.id)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label={t("wishlist.edit")}
        >
          {t("common.edit")}
        </button>
        <button
          onClick={() => onDelete(item.id)}
          className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
          aria-label={t("wishlist.delete")}
        >
          {t("common.delete")}
        </button>
      </div>
    </article>
  );
}
