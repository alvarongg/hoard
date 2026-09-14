import { useTranslation } from "react-i18next";
import type { CatalogItem, CollectionItem } from "../../types/item";
import { ItemCard } from "./ItemCard";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { ErrorMessage } from "../ui/ErrorMessage";
import { EmptyState } from "../ui/EmptyState";

interface ItemListProps {
  items: CollectionItem[];
  isLoading: boolean;
  error: Error | null;
  /** Catalog items used to resolve titles for each collection item. */
  catalogItems?: CatalogItem[];
  onEdit?: (id: string) => void;
}

export function ItemList({
  items,
  isLoading,
  error,
  catalogItems = [],
  onEdit,
}: ItemListProps) {
  const { t } = useTranslation();
  const byId = new Map(catalogItems.map((c) => [c.id, c]));

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
      {items.map((item) => {
        const catalogItem = byId.get(item.catalogItemId);
        return (
          <ItemCard
            key={item.id}
            item={item}
            catalogTitle={catalogItem?.title}
            onEdit={onEdit}
          />
        );
      })}
    </div>
  );
}
