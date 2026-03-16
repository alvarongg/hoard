import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { collectionItemsApi } from "../services/collectionItemsApi";
import type {
  CollectionItem,
  CollectionItemCreate,
  CollectionItemUpdate,
} from "../types/item";

function itemsKey(collectionId: string) {
  return ["collections", collectionId, "items"] as const;
}

export function useCollectionItems(collectionId: string) {
  const queryClient = useQueryClient();
  const key = itemsKey(collectionId);

  const query = useQuery<CollectionItem[], Error>({
    queryKey: key,
    queryFn: () => collectionItemsApi.list(collectionId),
    enabled: !!collectionId,
  });

  const addItem = useMutation<CollectionItem, Error, CollectionItemCreate>({
    mutationFn: (data) => collectionItemsApi.add(collectionId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });

  const updateItem = useMutation<
    CollectionItem,
    Error,
    { id: string; data: CollectionItemUpdate }
  >({
    mutationFn: ({ id, data }) => collectionItemsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });

  const removeItem = useMutation<void, Error, string>({
    mutationFn: (id) => collectionItemsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });

  return { ...query, addItem, updateItem, removeItem };
}
