import { useMemo } from "react";
import { useCatalogs } from "./useCatalogs";
import type { Catalog } from "../types/catalog";

interface UseCollectionCatalogResult {
  catalog: Catalog | null;
  catalogId: string | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Resolves the catalog a collection draws its items from.
 *
 * A collection is bound to a catalog indirectly: `restrictedToSubCategoryId`
 * points at the sub-category, and catalogs belong to a sub-category. When the
 * collection is not restricted to a sub-category (multi-category or mixed
 * collections) no single catalog can be resolved and `catalogId` is `null`.
 */
export function useCollectionCatalog(
  subCategoryId: string | null | undefined,
): UseCollectionCatalogResult {
  const catalogs = useCatalogs();

  const catalog = useMemo<Catalog | null>(() => {
    if (!subCategoryId) return null;

    const match = catalogs.data?.find(
      (candidate) =>
        candidate.subCategoryId === subCategoryId && candidate.isActive,
    );

    return match ?? null;
  }, [catalogs.data, subCategoryId]);

  return {
    catalog,
    catalogId: catalog?.id ?? null,
    isLoading: catalogs.isLoading,
    error: catalogs.error,
  };
}
