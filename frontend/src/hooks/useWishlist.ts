import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wishlistApi, WishlistFilters } from "../services/wishlistApi";
import type {
  WishlistItem,
  WishlistItemCreate,
  WishlistItemUpdate,
  WishlistItemDetail,
  WishlistAcquire,
} from "../types/wishlist";

const WISHLIST_KEY = ["wishlist"] as const;

export function useWishlist(filters?: WishlistFilters) {
  const queryClient = useQueryClient();

  const query = useQuery<WishlistItem[], Error>({
    queryKey: filters ? [...WISHLIST_KEY, filters] : WISHLIST_KEY,
    queryFn: () => wishlistApi.list(filters),
  });

  const create = useMutation<WishlistItem, Error, WishlistItemCreate>({
    mutationFn: (data) => wishlistApi.create(data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: WISHLIST_KEY }),
  });

  const update = useMutation<
    WishlistItem,
    Error,
    { id: string; data: WishlistItemUpdate }
  >({
    mutationFn: ({ id, data }) => wishlistApi.update(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: WISHLIST_KEY }),
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (id) => wishlistApi.remove(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: WISHLIST_KEY }),
  });

  return { ...query, create, update, remove };
}

export function useWishlistItem(id: string | undefined) {
  const queryClient = useQueryClient();

  const query = useQuery<WishlistItemDetail, Error>({
    queryKey: [...WISHLIST_KEY, id],
    queryFn: () => wishlistApi.get(id!),
    enabled: !!id,
  });

  const acquire = useMutation<
    WishlistItem,
    Error,
    { id: string; data: WishlistAcquire }
  >({
    mutationFn: ({ id, data }) => wishlistApi.acquire(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WISHLIST_KEY });
    },
  });

  return { ...query, acquire };
}
