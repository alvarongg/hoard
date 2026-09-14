import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wishlistApi } from "../services/wishlistApi";
import type { Sighting, SightingCreate, SightingUpdate } from "../types/wishlist";

const WISHLIST_KEY = ["wishlist"] as const;

export function useSightings(wishlistItemId: string | undefined) {
  const queryClient = useQueryClient();

  const query = useQuery<Sighting[], Error>({
    queryKey: [...WISHLIST_KEY, wishlistItemId, "sightings"],
    queryFn: () => wishlistApi.listSightings(wishlistItemId!),
    enabled: !!wishlistItemId,
  });

  const create = useMutation<
    Sighting,
    Error,
    { wishlistItemId: string; data: Omit<SightingCreate, "wishlistItemId"> }
  >({
    mutationFn: ({ wishlistItemId, data }) =>
      wishlistApi.createSighting(wishlistItemId, data),
    onSuccess: (_, variables) => {
      // Invalidate the sightings list
      queryClient.invalidateQueries({
        queryKey: [...WISHLIST_KEY, variables.wishlistItemId, "sightings"],
      });
      // Invalidate the wishlist item detail to refresh aggregates
      queryClient.invalidateQueries({
        queryKey: [...WISHLIST_KEY, variables.wishlistItemId],
      });
    },
  });

  const update = useMutation<
    Sighting,
    Error,
    { sightingId: string; wishlistItemId: string; data: SightingUpdate }
  >({
    mutationFn: ({ sightingId, data }) =>
      wishlistApi.updateSighting(sightingId, data),
    onSuccess: (_, variables) => {
      // Invalidate the sightings list
      queryClient.invalidateQueries({
        queryKey: [...WISHLIST_KEY, variables.wishlistItemId, "sightings"],
      });
      // Invalidate the wishlist item detail to refresh aggregates
      queryClient.invalidateQueries({
        queryKey: [...WISHLIST_KEY, variables.wishlistItemId],
      });
    },
  });

  const remove = useMutation<
    void,
    Error,
    { sightingId: string; wishlistItemId: string }
  >({
    mutationFn: ({ sightingId }) => wishlistApi.removeSighting(sightingId),
    onSuccess: (_, variables) => {
      // Invalidate the sightings list
      queryClient.invalidateQueries({
        queryKey: [...WISHLIST_KEY, variables.wishlistItemId, "sightings"],
      });
      // Invalidate the wishlist item detail to refresh aggregates
      queryClient.invalidateQueries({
        queryKey: [...WISHLIST_KEY, variables.wishlistItemId],
      });
    },
  });

  return { ...query, create, update, remove };
}
