import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useWishlistItem } from "../hooks/useWishlist";
import { useAcquireAndAdd } from "../hooks/useCollectorWorkflow";
import { useSightings } from "../hooks/useSightings";
import { AddToCollectionForm } from "../components/collector/AddToCollectionForm";
import type { AddToCollectionResult } from "../components/collector/AddToCollectionForm";
import { PriceAggregatesPanel } from "../components/wishlist/PriceAggregatesPanel";
import { SightingList } from "../components/wishlist/SightingList";
import { SightingForm } from "../components/wishlist/SightingForm";
import { AcquireDialog } from "../components/wishlist/AcquireDialog";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Modal } from "../components/ui/Modal";
import { Badge } from "../components/ui/Badge";
import { PriorityBadge } from "../components/wishlist/PriorityBadge";
import { UrgencyBadge } from "../components/wishlist/UrgencyBadge";
import type { SightingCreate, SightingUpdate, Sighting } from "../types/wishlist";

/**
 * WishlistDetailPage - Page component for viewing a single wishlist item with sightings.
 *
 * Features:
 * - Price aggregates panel
 * - List of sightings sorted by date
 * - Create, edit, delete sightings
 * - Mark as acquired dialog
 */
export function WishlistDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [isSightingFormOpen, setIsSightingFormOpen] = useState(false);
  const [editingSighting, setEditingSighting] = useState<Sighting | null>(null);
  const [isAcquireDialogOpen, setIsAcquireDialogOpen] = useState(false);
  const [isGotItOpen, setIsGotItOpen] = useState(false);
  const acquireAndAdd = useAcquireAndAdd(id ?? "");

  const {
    data: item,
    isLoading: isItemLoading,
    error: itemError,
    acquire,
  } = useWishlistItem(id);

  const {
    data: sightings,
    isLoading: isSightingsLoading,
    error: sightingsError,
    create: createSighting,
    update: updateSighting,
    remove: removeSighting,
  } = useSightings(id);

  const handleCreateSighting = () => {
    setEditingSighting(null);
    setIsSightingFormOpen(true);
  };

  const handleEditSighting = (sighting: Sighting) => {
    setEditingSighting(sighting);
    setIsSightingFormOpen(true);
  };

  const handleDeleteSighting = async (sightingId: string) => {
    if (window.confirm(t("wishlist.sightings.deleteConfirm"))) {
      await removeSighting.mutateAsync({ sightingId, wishlistItemId: id! });
    }
  };

  const handleSightingSubmit = async (data: SightingCreate | SightingUpdate) => {
    if (editingSighting) {
      await updateSighting.mutateAsync({
        sightingId: editingSighting.id,
        wishlistItemId: id!,
        data: data as SightingUpdate,
      });
    } else {
      await createSighting.mutateAsync({
        wishlistItemId: id!,
        data: data as Omit<SightingCreate, "wishlistItemId">,
      });
    }
    setIsSightingFormOpen(false);
    setEditingSighting(null);
  };

  const handleAcquire = async (collectionItemId: string) => {
    await acquire.mutateAsync({
      id: id!,
      data: { acquiredCollectionItemId: collectionItemId },
    });
    setIsAcquireDialogOpen(false);
  };

  const handleGotIt = (result: AddToCollectionResult) => {
    acquireAndAdd.mutate(
      {
        collectionItem: result.data,
        removeFromWishlist: result.removeFromWishlist,
      },
      { onSuccess: () => setIsGotItOpen(false) },
    );
  };

  const formatPrice = (price: number | null, currency: string) => {
    if (price === null) return null;
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format(price);
  };

  const isLoading = isItemLoading || isSightingsLoading;
  const error = itemError || sightingsError;

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error.message} />;
  if (!item) return <ErrorMessage message={t("errors.wishlist.notFound")} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link
          to="/wishlist"
          className="text-sm text-blue-600 hover:underline"
        >
          {t("wishlist.backToList")}
        </Link>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">
                {t("wishlist.itemTitle", { id: item.id.slice(0, 8) })}
              </h1>
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

          {!item.isAcquired && (
            <button
              onClick={() => setIsAcquireDialogOpen(true)}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              {t("wishlist.acquire.button")}
            </button>
          )}
          {!item.isAcquired && (
            <button
              onClick={() => setIsGotItOpen(true)}
              className="ml-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {t("collector.wishlist.gotIt")}
            </button>
          )}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {item.maxPrice !== null && (
            <div>
              <dt className="text-sm font-medium text-gray-500">{t("wishlist.budget")}</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {formatPrice(item.maxPrice, item.currency)}
              </dd>
            </div>
          )}

          {item.desiredCondition && (
            <div>
              <dt className="text-sm font-medium text-gray-500">{t("wishlist.condition")}</dt>
              <dd className="mt-1 text-lg text-gray-900">{item.desiredCondition}</dd>
            </div>
          )}

          <div>
            <dt className="text-sm font-medium text-gray-500">{t("wishlist.completeness")}</dt>
            <dd className="mt-1 text-lg text-gray-900">
              {item.mustBeComplete ? t("wishlist.mustBeComplete") : t("wishlist.anyCompleteness")}
            </dd>
          </div>
        </div>

        {item.notes && (
          <div className="mt-4">
            <dt className="text-sm font-medium text-gray-500">{t("wishlist.notes")}</dt>
            <dd className="mt-1 text-gray-900">{item.notes}</dd>
          </div>
        )}

        {item.searchNotes && (
          <div className="mt-4">
            <dt className="text-sm font-medium text-gray-500">{t("wishlist.searchNotes")}</dt>
            <dd className="mt-1 text-gray-900">{item.searchNotes}</dd>
          </div>
        )}
      </div>

      <PriceAggregatesPanel aggregates={item.priceAggregates} currency={item.currency} />

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{t("wishlist.sightings.title")}</h2>
          <button
            onClick={handleCreateSighting}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {t("wishlist.sightings.create")}
          </button>
        </div>

        {sightings && (
          <SightingList
            sightings={sightings}
            onEdit={handleEditSighting}
            onDelete={handleDeleteSighting}
          />
        )}
      </section>

      <Modal
        isOpen={isSightingFormOpen}
        onClose={() => setIsSightingFormOpen(false)}
        title={editingSighting ? t("wishlist.sightings.edit") : t("wishlist.sightings.create")}
      >
        <SightingForm
          sighting={editingSighting}
          onSubmit={handleSightingSubmit}
          onCancel={() => setIsSightingFormOpen(false)}
          isLoading={createSighting.isPending || updateSighting.isPending}
        />
      </Modal>

      <AcquireDialog
        item={item}
        isOpen={isAcquireDialogOpen}
        onClose={() => setIsAcquireDialogOpen(false)}
        onConfirm={handleAcquire}
        isLoading={acquire.isPending}
      />

      <Modal
        isOpen={isGotItOpen}
        onClose={() => setIsGotItOpen(false)}
        title={t("collector.wishlist.gotIt")}
      >
        <AddToCollectionForm
          catalogItemId={item.catalogItemId}
          fixedCollectionId={item.collectionId}
          showWishlistToggle
          isLoading={acquireAndAdd.isPending}
          onSubmit={handleGotIt}
          onCancel={() => setIsGotItOpen(false)}
        />
      </Modal>
    </div>
  );
}
