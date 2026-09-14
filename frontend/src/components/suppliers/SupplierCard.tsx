import { useTranslation } from "react-i18next";
import type { Supplier } from "../../types/supplier";
import { Badge } from "../ui/Badge";
import { FavoriteToggle } from "./FavoriteToggle";

interface SupplierCardProps {
  supplier: Supplier;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onToggleFavorite: (id: string, currentFavorite: boolean) => void;
}

const SUPPLIER_TYPE_LABELS: Record<string, string> = {
  online: "suppliers.typeOptions.online",
  physical_store: "suppliers.typeOptions.store",
  marketplace: "suppliers.typeOptions.market",
  private_seller: "suppliers.typeOptions.individual",
  auction: "suppliers.typeOptions.other",
};

/**
 * SupplierCard - Card component for displaying supplier information.
 *
 * Features:
 * - Displays supplier name, type, country, city, and rating
 * - Toggle favorite functionality
 * - Edit and delete actions
 * - Accessible with proper ARIA attributes
 */
export function SupplierCard({
  supplier,
  onEdit,
  onDelete,
  onToggleFavorite,
}: SupplierCardProps) {
  const { t } = useTranslation();
  const headingId = `supplier-${supplier.id}`;

  const typeLabel = supplier.type
    ? t(SUPPLIER_TYPE_LABELS[supplier.type] ?? supplier.type)
    : null;

  const location = [supplier.city, supplier.country]
    .filter(Boolean)
    .join(", ");

  return (
    <article
      aria-labelledby={headingId}
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h2 id={headingId} className="text-lg font-semibold text-gray-900">
            {supplier.name}
          </h2>
          {typeLabel && (
            <Badge label={typeLabel} tone="neutral" className="mt-1" />
          )}
        </div>
        <FavoriteToggle
          isFavorite={supplier.isFavorite}
          onToggle={() => onToggleFavorite(supplier.id, supplier.isFavorite)}
          ariaLabel={t("suppliers.favorite")}
        />
      </div>

      {location && (
        <p className="mt-2 text-sm text-gray-600">{location}</p>
      )}

      {supplier.rating !== null && supplier.rating !== undefined && (
        <div className="mt-2 flex items-center gap-1 text-sm text-gray-600">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="h-4 w-4 text-yellow-500"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10.868 2.884c-.321-.772-1.415-.772-1.736 0l-1.83 4.401-4.753.381c-.833.067-1.171 1.107-.536 1.651l3.62 3.102-1.106 4.637c-.194.813.691 1.456 1.405 1.02L10 15.591l4.069 2.485c.713.436 1.598-.207 1.404-1.02l-1.106-4.637 3.62-3.102c.635-.544.297-1.584-.536-1.65l-4.752-.382-1.831-4.401Z"
              clipRule="evenodd"
            />
          </svg>
          <span>
            {supplier.rating.toFixed(1)} / 5.0
          </span>
        </div>
      )}

      {supplier.website && (
        <a
          href={supplier.website}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 block text-sm text-blue-600 hover:underline"
        >
          {supplier.website}
        </a>
      )}

      <div className="mt-4 flex gap-2">
        <button
          onClick={() => onEdit(supplier.id)}
          aria-label={t("suppliers.edit")}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {t("common.edit")}
        </button>
        <button
          onClick={() => onDelete(supplier.id)}
          aria-label={t("suppliers.delete")}
          className="rounded-md bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          {t("common.delete")}
        </button>
      </div>
    </article>
  );
}
