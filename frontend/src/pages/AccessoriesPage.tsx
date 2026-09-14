import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { AccessoryCard } from "../components/accessories/AccessoryCard";
import { AccessoryForm } from "../components/accessories/AccessoryForm";
import { LowStockList } from "../components/accessories/LowStockList";
import { useAccessories, useLowStock } from "../hooks/useAccessories";
import type { Accessory } from "../types/accessory";

export function AccessoriesPage() {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch, create, update, remove } =
    useAccessories();
  const lowStock = useLowStock();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Accessory | null>(null);

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
  };

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("accessories.title")}
        </h1>
        <Button onClick={() => setShowForm(true)}>{t("accessories.add")}</Button>
      </div>

      {lowStock.data && lowStock.data.length > 0 && (
        <div className="mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-950">
          <LowStockList entries={lowStock.data} />
        </div>
      )}

      <section aria-label={t("accessories.title")} className="mt-6">
        {isLoading && <LoadingSpinner />}
        {error && (
          <ErrorMessage
            message={t("errors.loadFailed")}
            onRetry={() => refetch()}
          />
        )}
        {!isLoading && !error && (data?.length ?? 0) === 0 && (
          <EmptyState title={t("accessories.empty")} />
        )}
        {!isLoading && !error && (data?.length ?? 0) > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data?.map((acc) => (
              <AccessoryCard
                key={acc.id}
                accessory={acc}
                onEdit={(a) => {
                  setEditing(a);
                  setShowForm(true);
                }}
                onDelete={(id) => remove.mutate(id)}
              />
            ))}
          </div>
        )}
      </section>

      <Modal
        isOpen={showForm}
        onClose={closeForm}
        title={editing ? t("accessories.title") : t("accessories.add")}
      >
        <AccessoryForm
          initialData={editing}
          isLoading={create.isPending || update.isPending}
          onCancel={closeForm}
          onSubmit={(payload) => {
            if (editing) {
              update.mutate(
                { id: editing.id, data: payload },
                { onSuccess: closeForm },
              );
            } else {
              create.mutate(payload, { onSuccess: closeForm });
            }
          }}
        />
      </Modal>
    </main>
  );
}
