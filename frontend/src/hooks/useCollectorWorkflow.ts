import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { collectorWorkflowApi } from "../services/collectorWorkflowApi";
import type { CollectionItemCreate } from "../types/item";
import type {
  CatalogQuickAdd,
  MaintenanceCreate,
  SupplierQuickAdd,
} from "../types/collectorWorkflow";

export function useOwnership(catalogItemId: string | undefined) {
  return useQuery({
    queryKey: ["ownership", catalogItemId],
    queryFn: () => collectorWorkflowApi.ownership(catalogItemId as string),
    enabled: Boolean(catalogItemId),
  });
}

export function usePriceLookup(catalogItemId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (url: string) =>
      collectorWorkflowApi.priceLookup(catalogItemId, url),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["priceHistory", catalogItemId] });
    },
  });
}

export function useQuickAddSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SupplierQuickAdd) =>
      collectorWorkflowApi.quickAddSupplier(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["suppliers"] });
      void qc.invalidateQueries({ queryKey: ["pending"] });
    },
  });
}

export function useCollectionCatalogs(collectionId: string | undefined) {
  return useQuery({
    queryKey: ["collectionCatalogs", collectionId],
    queryFn: () =>
      collectorWorkflowApi.listCatalogs(collectionId as string),
    enabled: Boolean(collectionId),
  });
}

export function useCollectionCatalogMutations(collectionId: string) {
  const qc = useQueryClient();
  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ["collectionCatalogs", collectionId] });

  const associate = useMutation({
    mutationFn: ({
      catalogId,
      isPrimary,
    }: {
      catalogId: string;
      isPrimary?: boolean;
    }) =>
      collectorWorkflowApi.associateCatalog(
        collectionId,
        catalogId,
        isPrimary ?? false,
      ),
    onSuccess: invalidate,
  });

  const dissociate = useMutation({
    mutationFn: (catalogId: string) =>
      collectorWorkflowApi.dissociateCatalog(collectionId, catalogId),
    onSuccess: invalidate,
  });

  const quickAdd = useMutation({
    mutationFn: (data: CatalogQuickAdd) =>
      collectorWorkflowApi.quickAddCatalog(collectionId, data),
    onSuccess: () => {
      void invalidate();
      void qc.invalidateQueries({ queryKey: ["pending"] });
    },
  });

  return { associate, dissociate, quickAdd };
}

export function useQuickAddItem(collectionId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      catalogId,
      title,
      collectionItem,
    }: {
      catalogId: string;
      title: string;
      collectionItem: CollectionItemCreate;
    }) =>
      collectorWorkflowApi.quickAddItem(
        collectionId,
        catalogId,
        title,
        collectionItem,
      ),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: ["collectionItems", collectionId],
      });
      void qc.invalidateQueries({ queryKey: ["pending"] });
    },
  });
}

export function useAcquireAndAdd(wishlistItemId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      collectionItem,
      removeFromWishlist,
    }: {
      collectionItem: CollectionItemCreate;
      removeFromWishlist: boolean;
    }) =>
      collectorWorkflowApi.acquireAndAdd(
        wishlistItemId,
        collectionItem,
        removeFromWishlist,
      ),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["wishlist"] });
    },
  });
}

export function useMaintenance(collectionItemId: string | undefined) {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ["maintenance", collectionItemId],
    queryFn: () =>
      collectorWorkflowApi.listMaintenance(collectionItemId as string),
    enabled: Boolean(collectionItemId),
  });
  const create = useMutation({
    mutationFn: (data: MaintenanceCreate) =>
      collectorWorkflowApi.createMaintenance(
        collectionItemId as string,
        data,
      ),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: ["maintenance", collectionItemId],
      });
    },
  });
  return { ...query, create };
}

export function usePending(entityType?: string) {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ["pending", entityType ?? "all"],
    queryFn: () => collectorWorkflowApi.listPending("open", entityType),
  });
  const resolve = useMutation({
    mutationFn: ({
      id,
      completedFields,
    }: {
      id: string;
      completedFields: string[];
    }) => collectorWorkflowApi.resolvePending(id, completedFields),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["pending"] });
    },
  });
  return { ...query, resolve };
}
