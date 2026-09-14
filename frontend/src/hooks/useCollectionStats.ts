import { useQuery } from "@tanstack/react-query";
import { collectionsApi } from "../services/collectionsApi";

/**
 * Hook to fetch statistics for a collection.
 * @param collectionId - The UUID of the collection.
 */
export function useCollectionStats(collectionId: string | undefined) {
  return useQuery({
    queryKey: ["collection", collectionId, "stats"],
    queryFn: () => collectionsApi.stats(collectionId!),
    enabled: !!collectionId,
  });
}
