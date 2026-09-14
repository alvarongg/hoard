import { useQueries } from "@tanstack/react-query";

import { catalogsApi } from "../services/catalogsApi";
import type { CatalogItem } from "../types/item";
import { useCollectionCatalogs } from "./useCollectorWorkflow";

/**
 * Aggregate the catalog items of every catalog associated with a collection
 * (via the N:M collection_catalogs link). Works for single_category,
 * multi_category and mixed collections alike — unlike deriving a single
 * catalog from the restricted sub-category.
 */
export function useCollectionCatalogItems(collectionId: string | undefined) {
  const { data: catalogs = [], isLoading: catalogsLoading } =
    useCollectionCatalogs(collectionId);

  const itemQueries = useQueries({
    queries: catalogs.map((c) => ({
      queryKey: ["catalogs", c.id, "items"],
      queryFn: () => catalogsApi.listItems(c.id),
      enabled: Boolean(c.id),
    })),
  });

  const items: CatalogItem[] = itemQueries.flatMap((q) => q.data ?? []);
  const isLoading = catalogsLoading || itemQueries.some((q) => q.isLoading);

  // A single primary catalog id for inline creation (first associated).
  const primaryCatalogId = catalogs[0]?.id ?? null;

  return { items, isLoading, primaryCatalogId, catalogs };
}
