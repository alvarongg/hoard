import { useTranslation } from "react-i18next";
import type { Sighting } from "../../types/wishlist";
import { Badge } from "../ui/Badge";

interface SightingListProps {
  sightings: Sighting[];
  onEdit: (sighting: Sighting) => void;
  onDelete: (sightingId: string) => void;
}

/**
 * SightingList - List component for displaying wishlist item sightings.
 *
 * Features:
 * - Displays price, condition, availability
 * - Shows contact and decision status
 * - Edit and delete actions
 */
export function SightingList({ sightings, onEdit, onDelete }: SightingListProps) {
  const { t } = useTranslation();

  if (sightings.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">
        {t("wishlist.sightings.empty")}
      </p>
    );
  }

  // Sort sightings by sightedAt descending
  const sortedSightings = [...sightings].sort((a, b) => {
    if (!a.sightedAt) return 1;
    if (!b.sightedAt) return -1;
    return new Date(b.sightedAt).getTime() - new Date(a.sightedAt).getTime();
  });

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(price);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <ul className="space-y-3" role="list">
      {sortedSightings.map((sighting) => (
        <li
          key={sighting.id}
          className="rounded-lg border border-gray-200 bg-white p-4"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-gray-900">
                  {formatPrice(sighting.price, sighting.currency)}
                </span>
                {sighting.isAvailable ? (
                  <Badge label={t("wishlist.sightings.available")} tone="success" />
                ) : (
                  <Badge label={t("wishlist.sightings.unavailable")} tone="neutral" />
                )}
              </div>

              {sighting.condition && (
                <p className="mt-1 text-sm text-gray-600">
                  {t("wishlist.sightings.condition")}: {sighting.condition}
                </p>
              )}

              {sighting.url && (
                <a
                  href={sighting.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 block text-sm text-blue-600 hover:underline"
                >
                  {t("wishlist.sightings.viewListing")}
                </a>
              )}

              <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                {sighting.sightedAt && (
                  <span>{t("wishlist.sightings.sighted")}: {formatDate(sighting.sightedAt)}</span>
                )}
                {sighting.contacted && (
                  <Badge
                    label={t("wishlist.sightings.contacted")}
                    tone="neutral"
                    className="text-xs"
                  />
                )}
                {sighting.decision && (
                  <Badge
                    label={t(`wishlist.sightings.decision.${sighting.decision}`)}
                    tone={sighting.decision === "buy" ? "success" : "neutral"}
                    className="text-xs"
                  />
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => onEdit(sighting)}
                className="rounded-md bg-gray-100 px-2 py-1 text-sm text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                aria-label={t("wishlist.sightings.edit")}
              >
                {t("common.edit")}
              </button>
              <button
                onClick={() => onDelete(sighting.id)}
                className="rounded-md bg-red-100 px-2 py-1 text-sm text-red-700 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
                aria-label={t("wishlist.sightings.delete")}
              >
                {t("common.delete")}
              </button>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
