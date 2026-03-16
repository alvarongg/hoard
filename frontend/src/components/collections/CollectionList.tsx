import { useTranslation } from "react-i18next";
import type { Collection } from "../../types/collection";
import { CollectionCard } from "./CollectionCard";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { ErrorMessage } from "../ui/ErrorMessage";
import { EmptyState } from "../ui/EmptyState";

interface CollectionListProps {
  collections: Collection[];
  isLoading: boolean;
  error: Error | null;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

export function CollectionList({
  collections,
  isLoading,
  error,
  onEdit,
  onDelete,
}: CollectionListProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={t("errors.loadFailed")} />;
  }

  if (collections.length === 0) {
    return (
      <EmptyState
        title={t("collections.empty")}
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {collections.map((collection) => (
        <CollectionCard
          key={collection.id}
          collection={collection}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
