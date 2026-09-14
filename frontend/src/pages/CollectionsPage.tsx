import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useCollections } from "../hooks/useCollections";
import { useMainCategories, useSubCategories } from "../hooks/useCategories";
import { CollectionList } from "../components/collections/CollectionList";
import { CollectionForm } from "../components/collections/CollectionForm";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { useAnnouncement } from "../hooks/useAnnouncement";

export function CollectionsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const announce = useAnnouncement();
  const { data, isLoading, error, create, remove } = useCollections();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedMainCategoryId, setSelectedMainCategoryId] = useState("");
  const mainCategories = useMainCategories();
  const subCategories = useSubCategories(selectedMainCategoryId);

  const handleEdit = useCallback(
    (id: string) => {
      navigate(`/collections/${id}`);
    },
    [navigate],
  );

  const handleDelete = useCallback(
    (id: string) => {
      if (window.confirm(t("collections.deleteConfirm"))) {
        remove.mutate(id, {
          onSuccess: () => announce(t("collections.announceDeleted")),
          onError: () =>
            announce(t("collections.announceDeleteError"), "assertive"),
        });
      }
    },
    [remove, t, announce],
  );

  const handleCreate = useCallback(
    (formData: { name: string; description: string; collectionType: string; restrictedToSubCategoryId: string }) => {
      create.mutate(
        {
          name: formData.name,
          description: formData.description || undefined,
          collectionType: formData.collectionType as "single_category" | "multi_category" | "mixed",
          restrictedToSubCategoryId: formData.restrictedToSubCategoryId || undefined,
        },
        { onSuccess: () => {
          setShowCreateModal(false);
          setSelectedMainCategoryId("");
          announce(t("collections.announceCreated", { name: formData.name }));
        },
          onError: () =>
            announce(t("collections.announceCreateError"), "assertive"),
        },
      );
    },
    [create, t, announce],
  );

  function handleCloseModal() {
    setShowCreateModal(false);
    setSelectedMainCategoryId("");
  }

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          {t("collections.title")}
        </h1>
        <Button
          onClick={() => setShowCreateModal(true)}
          aria-label={t("collections.create")}
        >
          {t("collections.create")}
        </Button>
      </div>

      <section className="mt-6" aria-label={t("collections.title")}>
        <h2 className="sr-only">{t("collections.title")}</h2>
        <CollectionList
          collections={data ?? []}
          isLoading={isLoading}
          error={error}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </section>

      <Modal
        isOpen={showCreateModal}
        onClose={handleCloseModal}
        title={t("collections.create")}
      >
        <CollectionForm
          mainCategories={mainCategories.data ?? []}
          subCategories={subCategories.data ?? []}
          onMainCategoryChange={setSelectedMainCategoryId}
          onSubmit={handleCreate}
          onCancel={handleCloseModal}
          isLoading={create.isPending}
        />
      </Modal>
    </main>
  );
}
