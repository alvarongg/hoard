import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import { useCollection } from "../hooks/useCollection";
import { useCollectionItems } from "../hooks/useCollectionItems";
import { useCatalogSearch } from "../hooks/useCatalogs";
import { ItemList } from "../components/items/ItemList";
import { ItemForm } from "../components/items/ItemForm";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import type { ItemCondition } from "../types/item";

export function CollectionDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const collection = useCollection(id ?? "");
  const items = useCollectionItems(id ?? "");
  const catalogSearch = useCatalogSearch("");
  const [showAddItemModal, setShowAddItemModal] = useState(false);

  const handleAddItem = useCallback(
    (formData: { catalogItemId: string; condition: ItemCondition; notes: string; purchasePrice: string }) => {
      items.addItem.mutate(
        {
          catalogItemId: formData.catalogItemId,
          condition: formData.condition,
          notes: formData.notes || undefined,
          purchasePrice: formData.purchasePrice
            ? Number(formData.purchasePrice)
            : undefined,
        },
        { onSuccess: () => setShowAddItemModal(false) },
      );
    },
    [items.addItem],
  );

  if (collection.isLoading) {
    return (
      <main>
        <LoadingSpinner />
      </main>
    );
  }

  if (collection.error) {
    return (
      <main>
        <ErrorMessage
          message={t("errors.loadFailed")}
          onRetry={() => collection.refetch()}
        />
      </main>
    );
  }

  if (!collection.data) {
    return (
      <main>
        <ErrorMessage message={t("errors.notFound")} />
      </main>
    );
  }

  return (
    <main>
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate("/collections")}
            className="text-sm text-blue-600 hover:underline"
            aria-label={t("navigation.collections")}
          >
            ← {t("navigation.collections")}
          </button>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">
            {collection.data.name}
          </h1>
          {collection.data.description && (
            <p className="mt-1 text-gray-600">
              {collection.data.description}
            </p>
          )}
        </div>
        <Button
          onClick={() => setShowAddItemModal(true)}
          aria-label={t("items.add")}
        >
          {t("items.add")}
        </Button>
      </div>

      <section aria-label={t("collections.items")} className="mt-6">
        <h2 className="text-lg font-semibold text-gray-900">
          {t("collections.items")}
        </h2>
        <div className="mt-3">
          <ItemList
            items={items.data ?? []}
            isLoading={items.isLoading}
            error={items.error}
          />
        </div>
      </section>

      <Modal
        isOpen={showAddItemModal}
        onClose={() => setShowAddItemModal(false)}
        title={t("items.add")}
      >
        <ItemForm
          catalogItems={catalogSearch.data ?? []}
          onSubmit={handleAddItem}
          onCancel={() => setShowAddItemModal(false)}
          isLoading={items.addItem.isPending}
        />
      </Modal>
    </main>
  );
}
