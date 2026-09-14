import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";

import { useCatalogItem } from "../hooks/useCatalogItem";
import { useCollections } from "../hooks/useCollections";
import { useOwnership, usePriceLookup } from "../hooks/useCollectorWorkflow";
import { useUpdateCatalogItem } from "../hooks/useUpdateCatalogItem";
import { usePriceHistory } from "../hooks/usePriceHistory";
import { useWishlist } from "../hooks/useWishlist";
import { collectionItemsApi } from "../services/collectionItemsApi";
import { AddToCollectionForm } from "../components/collector/AddToCollectionForm";
import type { AddToCollectionResult } from "../components/collector/AddToCollectionForm";
import { CatalogItemEditForm } from "../components/catalog/CatalogItemEditForm";
import { PriceHistoryTable } from "../components/priceHistory/PriceHistoryTable";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Input } from "../components/ui/Input";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { Modal } from "../components/ui/Modal";
import { Select } from "../components/ui/Select";

export function CatalogItemDetailPage() {
  const { t } = useTranslation();
  const { itemId } = useParams<{ catalogId: string; itemId: string }>();
  const { data: item, isLoading, isError } = useCatalogItem(itemId);
  const { data: ownership } = useOwnership(itemId);
  const priceHistory = usePriceHistory(itemId);
  const priceLookup = usePriceLookup(itemId as string);
  const { data: collections = [] } = useCollections();
  const wishlist = useWishlist();

  const [showAdd, setShowAdd] = useState(false);
  const [showWishlist, setShowWishlist] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const updateItem = useUpdateCatalogItem(itemId as string);
  const [wishlistCollection, setWishlistCollection] = useState("");
  const [priceUrl, setPriceUrl] = useState("");
  const [addError, setAddError] = useState<string | null>(null);

  if (isLoading) return <LoadingSpinner />;
  if (isError || !item) return <ErrorMessage message={t("common.error")} />;

  const handleAdd = async (result: AddToCollectionResult) => {
    setAddError(null);
    try {
      const created = await collectionItemsApi.add(
        result.collectionId,
        result.data,
      );
      if (result.maintenance) {
        await collectorCreateMaintenance(created.id, result.maintenance);
      }
      setShowAdd(false);
    } catch {
      setAddError(t("collector.addToCollection.error"));
    }
  };

  const collectorCreateMaintenance = async (
    collectionItemId: string,
    maintenance: { maintenanceType: string; dueDate: string },
  ) => {
    const { collectorWorkflowApi } = await import(
      "../services/collectorWorkflowApi"
    );
    await collectorWorkflowApi.createMaintenance(collectionItemId, maintenance);
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold">{item.title}</h1>
        {item.subtitle && <p className="text-gray-600">{item.subtitle}</p>}
        <div className="mt-1 flex flex-wrap gap-2 text-sm">
          {item.region && <Badge label={item.region} tone="neutral" />}
          {item.manufacturer && (
            <Badge label={item.manufacturer} tone="neutral" />
          )}
          {item.publisher && <Badge label={item.publisher} tone="neutral" />}
        </div>
      </div>

      {ownership?.owned ? (
        <Card>
          <p className="font-medium text-green-700">
            {t("collector.ownership.owned", { count: ownership.count })}
          </p>
          <ul className="mt-1 list-disc pl-5 text-sm">
            {ownership.entries.map((e) => (
              <li key={e.collectionItemId}>
                {e.collectionName} — {t(`items.${e.condition}`)}
              </li>
            ))}
          </ul>
        </Card>
      ) : (
        <p className="text-sm text-gray-500">
          {t("collector.ownership.notOwned")}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => setShowAdd(true)}>
          {t("collector.actions.addToCollection")}
        </Button>
        <Button variant="secondary" onClick={() => setShowWishlist(true)}>
          {t("collector.actions.addToWishlist")}
        </Button>
        <Button variant="secondary" onClick={() => setShowEdit(true)}>
          {t("catalogItemEdit.edit")}
        </Button>
      </div>

      {item.variation && (
        <p className="text-sm">
          <span className="font-medium">{t("catalogItemEdit.variation")}:</span>{" "}
          {item.variation}
          {item.variationDetails ? ` — ${item.variationDetails}` : ""}
        </p>
      )}

      {item.description && <p>{item.description}</p>}

      <Card>
        <h2 className="mb-2 text-lg font-semibold">
          {t("collector.price.title")}
        </h2>
        <div className="mb-3 flex items-end gap-2">
          <div className="flex-1">
            <Input
              label={t("collector.price.url")}
              placeholder="https://www.pricecharting.com/game/famicom/..."
              value={priceUrl}
              onChange={(e) => setPriceUrl(e.target.value)}
            />
          </div>
          <Button
            type="button"
            onClick={() => priceLookup.mutate(priceUrl)}
            disabled={!priceUrl.trim() || priceLookup.isPending}
          >
            {t("collector.price.lookup")}
          </Button>
        </div>
        {priceLookup.isError && (
          <p className="mb-2 text-sm text-red-600">
            {t("collector.price.error")}
          </p>
        )}
        <PriceHistoryTable entries={priceHistory.data ?? []} />
      </Card>

      <Modal
        isOpen={showAdd}
        onClose={() => setShowAdd(false)}
        title={t("collector.actions.addToCollection")}
      >
        {addError && <ErrorMessage message={addError} />}
        <AddToCollectionForm
          catalogItemId={item.id}
          onSubmit={handleAdd}
          onCancel={() => setShowAdd(false)}
        />
      </Modal>

      <Modal
        isOpen={showWishlist}
        onClose={() => setShowWishlist(false)}
        title={t("collector.actions.addToWishlist")}
      >
        <div className="flex flex-col gap-3">
          <Select
            label={t("collector.addToCollection.collection")}
            value={wishlistCollection}
            onChange={(e) => setWishlistCollection(e.target.value)}
            options={[
              { value: "", label: t("collector.addToCollection.chooseCollection") },
              ...collections.map((c) => ({ value: c.id, label: c.name })),
            ]}
          />
          <div className="flex gap-2">
            <Button
              type="button"
              disabled={!wishlistCollection || wishlist.create.isPending}
              onClick={() =>
                wishlist.create.mutate(
                  {
                    collectionId: wishlistCollection,
                    catalogItemId: item.id,
                  },
                  { onSuccess: () => setShowWishlist(false) },
                )
              }
            >
              {t("collector.actions.addToWishlist")}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowWishlist(false)}
            >
              {t("common.cancel")}
            </Button>
          </div>
        </div>
      </Modal>
      <Modal
        isOpen={showEdit}
        onClose={() => setShowEdit(false)}
        title={t("catalogItemEdit.edit")}
      >
        <CatalogItemEditForm
          item={item}
          isLoading={updateItem.isPending}
          onSubmit={(data) =>
            updateItem.mutate(data, { onSuccess: () => setShowEdit(false) })
          }
          onCancel={() => setShowEdit(false)}
        />
      </Modal>
    </div>
  );
}
