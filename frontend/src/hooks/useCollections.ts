import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { collectionsApi } from "../services/collectionsApi";
import type {
  Collection,
  CollectionCreate,
  CollectionUpdate,
} from "../types/collection";

const COLLECTIONS_KEY = ["collections"] as const;

export function useCollections() {
  const queryClient = useQueryClient();

  const query = useQuery<Collection[], Error>({
    queryKey: COLLECTIONS_KEY,
    queryFn: () => collectionsApi.list(),
  });

  const create = useMutation<Collection, Error, CollectionCreate>({
    mutationFn: (data) => collectionsApi.create(data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY }),
  });

  const update = useMutation<
    Collection,
    Error,
    { id: string; data: CollectionUpdate }
  >({
    mutationFn: ({ id, data }) => collectionsApi.update(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY }),
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (id) => collectionsApi.delete(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY }),
  });

  return { ...query, create, update, remove };
}
