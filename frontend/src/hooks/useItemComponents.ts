/**
 * React Query hooks for item components.
 *
 * Provides hooks for fetching and mutating item components.
 * Mutations return the completeness result for updating UI state.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { itemComponentsApi } from "../services/itemComponentsApi";
import type {
  ItemComponentCreate,
  ItemComponentUpdate,
  CompletenessResult,
} from "../types/itemComponent";

/**
 * Hook for fetching the component template for a collection item.
 */
export function useComponentTemplate(collectionItemId: string | undefined) {
  return useQuery({
    queryKey: ["componentTemplate", collectionItemId],
    queryFn: () =>
      collectionItemId
        ? itemComponentsApi.template(collectionItemId)
        : Promise.resolve([]),
    enabled: !!collectionItemId,
  });
}

/**
 * Hook for fetching all components for a collection item.
 */
export function useItemComponents(collectionItemId: string | undefined) {
  return useQuery({
    queryKey: ["itemComponents", collectionItemId],
    queryFn: () =>
      collectionItemId
        ? itemComponentsApi.list(collectionItemId)
        : Promise.resolve([]),
    enabled: !!collectionItemId,
  });
}

/**
 * Hook for managing item component mutations.
 *
 * All mutations return the completeness result for updating UI badges
 * without needing to refetch the collection item.
 */
export function useItemComponentMutations(collectionItemId: string) {
  const queryClient = useQueryClient();

  const upsert = useMutation({
    mutationFn: (data: ItemComponentCreate) =>
      itemComponentsApi.upsert(collectionItemId, data),
    onSuccess: () => {
      // Invalidate both the components list and template
      queryClient.invalidateQueries({
        queryKey: ["itemComponents", collectionItemId],
      });
      queryClient.invalidateQueries({
        queryKey: ["componentTemplate", collectionItemId],
      });
    },
  });

  const update = useMutation({
    mutationFn: ({
      componentId,
      data,
    }: {
      componentId: string;
      data: ItemComponentUpdate;
    }) => itemComponentsApi.update(componentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["itemComponents", collectionItemId],
      });
      queryClient.invalidateQueries({
        queryKey: ["componentTemplate", collectionItemId],
      });
    },
  });

  const remove = useMutation({
    mutationFn: (componentId: string) => itemComponentsApi.remove(componentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["itemComponents", collectionItemId],
      });
      queryClient.invalidateQueries({
        queryKey: ["componentTemplate", collectionItemId],
      });
    },
  });

  return {
    upsert,
    update,
    remove,
  };
}

/**
 * Callback type for completeness changes.
 */
export type OnCompletenessChange = (result: CompletenessResult) => void;
