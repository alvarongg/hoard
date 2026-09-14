import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import { useCollection } from "../hooks/useCollection";
import { useCollectionItems } from "../hooks/useCollectionItems";
import { useCollectionCatalog } from "../hooks/useCollectionCatalog";
import { useCatalogItems } from "../hooks/useCatalogItems";
import { ItemList } from "../components/items/ItemList";
import { ItemForm } from "../components/items/ItemForm";
import { TransactionList } from "../components/transactions/TransactionList";
import { TransactionForm } from "../components/transactions/TransactionForm";
import { InvestmentSummary } from "../components/transactions/InvestmentSummary";
import { useTransactions, useItemInvestment } from "../hooks/useTransactions";
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
  const { catalogId } = useCollectionCatalog(
    collection.data?.restrictedToSubCategoryId,
  );
  const catalogItems = useCatalogItems(catalogId ?? "");
  const [showAddItemModal, setShowAddItemModal] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

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

      {(items.data?.length ?? 0) > 0 && (
        <section aria-label={t("transactions.title")} className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("transactions.title")}
          </h2>
          <label className="mt-2 block text-sm">
            <span className="mr-2 text-gray-700 dark:text-gray-300">
              {t("items.title")}
            </span>
            <select
              className="rounded-md border border-gray-300 px-2 py-1 text-sm"
              value={selectedItemId ?? ""}
              onChange={(e) => setSelectedItemId(e.target.value || null)}
            >
              <option value="">—</option>
              {items.data?.map((it) => (
                <option key={it.id} value={it.id}>
                  {`${it.condition} · ${it.id.slice(0, 8)}`}
                </option>
              ))}
            </select>
          </label>
          {selectedItemId && (
            <TransactionsSection collectionItemId={selectedItemId} />
          )}
        </section>
      )}

      <Modal
        isOpen={showAddItemModal}
        onClose={() => setShowAddItemModal(false)}
        title={t("items.add")}
      >
        <ItemForm
          catalogItems={catalogItems.data ?? []}
          catalogId={catalogId}
          onSubmit={handleAddItem}
          onCancel={() => setShowAddItemModal(false)}
          isLoading={items.addItem.isPending}
        />
      </Modal>
    </main>
  );
}

interface TransactionsSectionProps {
  collectionItemId: string;
}

function TransactionsSection({ collectionItemId }: TransactionsSectionProps) {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch, create, remove } =
    useTransactions(collectionItemId);
  const investment = useItemInvestment(collectionItemId);
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between">
        <Button onClick={() => setShowForm((s) => !s)}>
          {t("transactions.add")}
        </Button>
      </div>

      {showForm && (
        <div className="mt-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <TransactionForm
            isLoading={create.isPending}
            onCancel={() => setShowForm(false)}
            onSubmit={(payload) =>
              create.mutate(payload, { onSuccess: () => setShowForm(false) })
            }
          />
        </div>
      )}

      {investment.data && (
        <div className="mt-4">
          <InvestmentSummary investment={investment.data} />
        </div>
      )}

      <div className="mt-4">
        {isLoading && <LoadingSpinner />}
        {error && (
          <ErrorMessage
            message={t("errors.loadFailed")}
            onRetry={() => refetch()}
          />
        )}
        {!isLoading && !error && (
          <TransactionList
            transactions={data ?? []}
            onDelete={(id) => remove.mutate(id)}
          />
        )}
      </div>
    </div>
  );
}
