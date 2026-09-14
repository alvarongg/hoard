import { useQuery } from "@tanstack/react-query";
import { collectionsApi } from "../services/collectionsApi";

/**
 * Hook to fetch collection items grouped by category.
 * @param collectionId - The UUID of the collection.
 */
export function useCollectionItemsGrouped(collectionId: string | undefined) {
  return useQuery({
    queryKey: ["collection", collectionId, "items-grouped"],
    queryFn: () => collectionsApi.itemsGrouped(collectionId!),
    enabled: !!collectionId,
  });
}
