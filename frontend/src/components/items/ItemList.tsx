import { useTranslation } from "react-i18next";
import type { CollectionItem } from "../../types/item";
import { ItemCard } from "./ItemCard";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { ErrorMessage } from "../ui/ErrorMessage";
import { EmptyState } from "../ui/EmptyState";

interface ItemListProps {
  items: CollectionItem[];
  isLoading: boolean;
  error: Error | null;
  onEdit?: (id: string) => void;
}

export function ItemList({ items, isLoading, error, onEdit }: ItemListProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={t("errors.loadFailed")} />;
  }

  if (items.length === 0) {
    return <EmptyState title={t("items.empty")} />;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <ItemCard key={item.id} item={item} onEdit={onEdit} />
      ))}
    </div>
  );
}
