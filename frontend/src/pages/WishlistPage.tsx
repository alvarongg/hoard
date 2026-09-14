import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useWishlist } from "../hooks/useWishlist";
import { WishlistCard } from "../components/wishlist/WishlistCard";
import { WishlistFilters } from "../components/wishlist/WishlistFilters";
import { WishlistForm } from "../components/wishlist/WishlistForm";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Modal } from "../components/ui/Modal";
import type { WishlistItemCreate, WishlistItemUpdate, Urgency } from "../types/wishlist";

/**
 * WishlistPage - Page component for viewing and managing wishlist items.
 *
 * Features:
 * - List of wishlist items with cards
 * - Filtering by priority, urgency, and status
 * - Create, edit, delete wishlist items
 */
export function WishlistPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Filter state
  const [priority, setPriority] = useState<number | undefined>();
  const [urgency, setUrgency] = useState<Urgency | undefined>();
  const [isActive, setIsActive] = useState<boolean | undefined>();
  const [includeAcquired, setIncludeAcquired] = useState(false);

  // Modal state
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<string | null>(null);

  const {
    data: items,
    isLoading,
    error,
    create,
    update,
    remove,
  } = useWishlist({
    priority,
    urgency,
    isActive,
    includeAcquired,
  });

  const handleCreate = () => {
    setEditingItem(null);
    setIsFormOpen(true);
  };

  const handleEdit = (id: string) => {
    setEditingItem(id);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm(t("wishlist.deleteConfirm"))) {
      await remove.mutateAsync(id);
    }
  };

  const handleView = (id: string) => {
    navigate(`/wishlist/${id}`);
  };

  const handleFormSubmit = async (data: WishlistItemCreate | WishlistItemUpdate) => {
    if (editingItem) {
      await update.mutateAsync({ id: editingItem, data: data as WishlistItemUpdate });
    } else {
      await create.mutateAsync(data as WishlistItemCreate);
    }
    setIsFormOpen(false);
    setEditingItem(null);
  };

  const handleClearFilters = () => {
    setPriority(undefined);
    setUrgency(undefined);
    setIsActive(undefined);
    setIncludeAcquired(false);
  };

  const editingItemData = editingItem ? items?.find((i) => i.id === editingItem) : null;

  return (
    <main className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t("wishlist.title")}</h1>
        <button
          onClick={handleCreate}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {t("wishlist.create")}
        </button>
      </header>

      <WishlistFilters
        priority={priority}
        urgency={urgency}
        isActive={isActive}
        includeAcquired={includeAcquired}
        onPriorityChange={setPriority}
        onUrgencyChange={setUrgency}
        onIsActiveChange={setIsActive}
        onIncludeAcquiredChange={setIncludeAcquired}
        onClear={handleClearFilters}
      />

      {isLoading && <LoadingSpinner />}

      {error && <ErrorMessage message={error.message} />}

      {items && items.length === 0 && (
        <p className="rounded-lg border border-gray-200 bg-white p-6 text-center text-gray-500">
          {t("wishlist.empty")}
        </p>
      )}

      {items && items.length > 0 && (
        <section aria-label={t("wishlist.title")}>
          <ul role="list" className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <li key={item.id}>
                <WishlistCard
                  item={item}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onView={handleView}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      <Modal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        title={editingItem ? t("wishlist.edit") : t("wishlist.create")}
      >
        <WishlistForm
          item={editingItemData}
          onSubmit={handleFormSubmit}
          onCancel={() => setIsFormOpen(false)}
          isLoading={create.isPending || update.isPending}
        />
      </Modal>
    </main>
  );
}
