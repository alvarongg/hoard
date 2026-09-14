import { fetchApi, toSnakeCase } from "./api";
import type { Catalog } from "../types/catalog";
import type { CollectionItem, CollectionItemCreate } from "../types/item";
import type { PriceHistoryEntry } from "../types/priceHistory";
import type { Supplier } from "../types/supplier";
import type {
  CatalogQuickAdd,
  MaintenanceCreate,
  MaintenanceSchedule,
  Ownership,
  Pending,
  SupplierQuickAdd,
} from "../types/collectorWorkflow";

export const collectorWorkflowApi = {
  // Ownership -------------------------------------------------------------
  ownership: (catalogItemId: string): Promise<Ownership> =>
    fetchApi<Ownership>(`/catalog-items/${catalogItemId}/ownership`),

  // Price lookup (on-demand PriceCharting) --------------------------------
  priceLookup: (catalogItemId: string, url: string): Promise<PriceHistoryEntry[]> =>
    fetchApi<PriceHistoryEntry[]>(`/catalog-items/${catalogItemId}/price-lookup`, {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  // Supplier quick-add ----------------------------------------------------
  quickAddSupplier: (data: SupplierQuickAdd): Promise<Supplier> =>
    fetchApi<Supplier>("/suppliers/quick", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  // Collection <-> catalog (N:M) -----------------------------------------
  listCatalogs: (collectionId: string): Promise<Catalog[]> =>
    fetchApi<Catalog[]>(`/collections/${collectionId}/catalogs`),

  associateCatalog: (
    collectionId: string,
    catalogId: string,
    isPrimary = false,
  ): Promise<Catalog> =>
    fetchApi<Catalog>(`/collections/${collectionId}/catalogs`, {
      method: "POST",
      body: JSON.stringify({ catalog_id: catalogId, is_primary: isPrimary }),
    }),

  dissociateCatalog: (collectionId: string, catalogId: string): Promise<void> =>
    fetchApi<void>(`/collections/${collectionId}/catalogs/${catalogId}`, {
      method: "DELETE",
    }),

  quickAddCatalog: (
    collectionId: string,
    data: CatalogQuickAdd,
  ): Promise<Catalog> =>
    fetchApi<Catalog>(`/collections/${collectionId}/catalogs/quick`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  // Quick add catalog item + collection item -----------------------------
  quickAddItem: (
    collectionId: string,
    catalogId: string,
    title: string,
    collectionItem: CollectionItemCreate,
  ): Promise<CollectionItem> =>
    fetchApi<CollectionItem>(`/collections/${collectionId}/items/quick`, {
      method: "POST",
      body: JSON.stringify({
        catalog_id: catalogId,
        title,
        collection_item: toSnakeCase(collectionItem),
      }),
    }),

  // Wishlist "ya lo conseguí" --------------------------------------------
  acquireAndAdd: (
    wishlistItemId: string,
    collectionItem: CollectionItemCreate,
    removeFromWishlist: boolean,
  ): Promise<unknown> =>
    fetchApi<unknown>(`/wishlist/${wishlistItemId}/acquire-and-add`, {
      method: "POST",
      body: JSON.stringify({
        collection_item: toSnakeCase(collectionItem),
        remove_from_wishlist: removeFromWishlist,
      }),
    }),

  // Maintenance -----------------------------------------------------------
  listMaintenance: (collectionItemId: string): Promise<MaintenanceSchedule[]> =>
    fetchApi<MaintenanceSchedule[]>(
      `/collection-items/${collectionItemId}/maintenance`,
    ),

  createMaintenance: (
    collectionItemId: string,
    data: MaintenanceCreate,
  ): Promise<MaintenanceSchedule> =>
    fetchApi<MaintenanceSchedule>(
      `/collection-items/${collectionItemId}/maintenance`,
      { method: "POST", body: JSON.stringify(toSnakeCase(data)) },
    ),

  dueMaintenance: (before?: string): Promise<MaintenanceSchedule[]> =>
    fetchApi<MaintenanceSchedule[]>(
      `/maintenance/due${before ? `?before=${before}` : ""}`,
    ),

  // Pending ---------------------------------------------------------------
  listPending: (
    status = "open",
    entityType?: string,
  ): Promise<Pending[]> => {
    const params = new URLSearchParams({ status });
    if (entityType) params.set("entity_type", entityType);
    return fetchApi<Pending[]>(`/pending?${params.toString()}`);
  },

  resolvePending: (
    pendingId: string,
    completedFields: string[],
  ): Promise<Pending> =>
    fetchApi<Pending>(`/pending/${pendingId}/resolve`, {
      method: "PUT",
      body: JSON.stringify({ completed_fields: completedFields }),
    }),
};
