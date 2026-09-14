import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSuppliers } from "../hooks/useSuppliers";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { Modal } from "../components/ui/Modal";
import { useAnnouncement } from "../hooks/useAnnouncement";
import { SupplierCard } from "../components/suppliers/SupplierCard";
import { SupplierForm } from "../components/suppliers/SupplierForm";
import { SupplierFilters } from "../components/suppliers/SupplierFilters";
import { Button } from "../components/ui/Button";
import type { Supplier, SupplierCreate, SupplierUpdate } from "../types/supplier";

/**
 * SuppliersPage - Page for managing suppliers.
 *
 * Features:
 * - List suppliers with filters (type, country, favorites)
 * - Create new supplier via modal form
 * - Edit existing supplier
 * - Delete supplier (with confirmation)
 * - Toggle favorite status with optimistic update
 * - Empty state when no suppliers exist
 * - Loading and error states
 */
export function SuppliersPage() {
  const { t } = useTranslation();
  const announce = useAnnouncement();

  // Filter state
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [countryFilter, setCountryFilter] = useState<string>("");
  const [favoritesOnly, setFavoritesOnly] = useState<boolean>(false);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [deletingSupplier, setDeletingSupplier] = useState<Supplier | null>(null);

  // Build filters object (only include non-empty filters)
  const filters = {
    ...(typeFilter && { type: typeFilter }),
    ...(countryFilter && { country: countryFilter }),
    ...(favoritesOnly && { isFavorite: true }),
  };

  const {
    data: suppliers,
    isLoading,
    error,
    refetch,
    create,
    update,
    remove,
    toggleFavorite,
  } = useSuppliers(Object.keys(filters).length > 0 ? filters : undefined);

  // Extract unique countries from suppliers for the filter dropdown
  const countries = suppliers
    ? [...new Set(suppliers.map((s) => s.country).filter(Boolean))].sort()
    : [];

  // Handlers
  function handleCreate() {
    setEditingSupplier(null);
    setIsModalOpen(true);
  }

  function handleEdit(id: string) {
    const supplier = suppliers?.find((s) => s.id === id);
    if (supplier) {
      setEditingSupplier(supplier);
      setIsModalOpen(true);
    }
  }

  function handleDelete(id: string) {
    const supplier = suppliers?.find((s) => s.id === id);
    if (supplier) {
      setDeletingSupplier(supplier);
    }
  }

  function handleConfirmDelete() {
    if (deletingSupplier) {
      remove.mutate(deletingSupplier.id, {
        onSuccess: () => {
          setDeletingSupplier(null);
          announce(t("suppliers.announceDeleted"));
        },
        onError: () =>
          announce(t("suppliers.announceDeleteError"), "assertive"),
      });
    }
  }

  function handleToggleFavorite(id: string, currentFavorite: boolean) {
    toggleFavorite.mutate({ id, currentFavorite });
  }

  function handleSubmit(data: SupplierCreate | SupplierUpdate) {
    if (editingSupplier) {
      update.mutate(
        { id: editingSupplier.id, data },
        {
          onSuccess: () => {
            setIsModalOpen(false);
            setEditingSupplier(null);
          },
        }
      );
    } else {
      create.mutate(data as SupplierCreate, {
        onSuccess: () => {
          setIsModalOpen(false);
          announce(
            t("suppliers.announceCreated", {
              name: (data as SupplierCreate).name,
            }),
          );
        },
        onError: () =>
          announce(t("suppliers.announceCreateError"), "assertive"),
      });
    }
  }

  function handleModalClose() {
    setIsModalOpen(false);
    setEditingSupplier(null);
  }

  // Loading state
  if (isLoading) {
    return (
      <main>
        <h1 className="text-2xl font-bold text-gray-900">
          {t("suppliers.title")}
        </h1>
        <LoadingSpinner />
      </main>
    );
  }

  // Error state
  if (error) {
    return (
      <main>
        <h1 className="text-2xl font-bold text-gray-900">
          {t("suppliers.title")}
        </h1>
        <ErrorMessage
          message={t("errors.loadFailed")}
          onRetry={() => refetch()}
        />
      </main>
    );
  }

  const isSubmitting = create.isPending || update.isPending;

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          {t("suppliers.title")}
        </h1>
        <Button onClick={handleCreate}>
          {t("suppliers.create")}
        </Button>
      </div>

      {suppliers && suppliers.length > 0 && (
        <div className="mt-4">
          <SupplierFilters
            typeFilter={typeFilter}
            countryFilter={countryFilter}
            favoritesOnly={favoritesOnly}
            countries={countries as string[]}
            onTypeChange={setTypeFilter}
            onCountryChange={setCountryFilter}
            onFavoritesChange={setFavoritesOnly}
          />
        </div>
      )}

      <div className="mt-6">
        {!suppliers || suppliers.length === 0 ? (
          <EmptyState
            title={t("suppliers.empty")}
            action={<Button onClick={handleCreate}>{t("suppliers.create")}</Button>}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {suppliers.map((supplier) => (
              <SupplierCard
                key={supplier.id}
                supplier={supplier}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        title={editingSupplier ? t("suppliers.edit") : t("suppliers.create")}
      >
        <SupplierForm
          initialData={editingSupplier}
          onSubmit={handleSubmit}
          onCancel={handleModalClose}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingSupplier}
        onClose={() => setDeletingSupplier(null)}
        title={t("suppliers.delete")}
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            {t("suppliers.deleteConfirm", { name: deletingSupplier?.name })}
          </p>
          {remove.isError && (
            <p className="text-sm text-red-600">
              {remove.error?.message || t("errors.deleteFailed")}
            </p>
          )}
          <div className="flex gap-2">
            <Button
              variant="danger"
              onClick={handleConfirmDelete}
              isLoading={remove.isPending}
            >
              {t("common.delete")}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setDeletingSupplier(null)}
            >
              {t("common.cancel")}
            </Button>
          </div>
        </div>
      </Modal>
    </main>
  );
}
