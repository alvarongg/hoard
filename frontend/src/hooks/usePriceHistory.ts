import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { priceHistoryApi } from "../services/priceHistoryApi";
import type {
  PriceHistoryEntry,
  PriceHistoryCreate,
  PriceHistoryFilters,
  LatestPriceEntry,
  ValueUpdateResult,
} from "../types/priceHistory";

const PRICE_HISTORY_KEY = ["price-history"] as const;

export function usePriceHistory(
  catalogItemId: string | undefined,
  filters?: PriceHistoryFilters,
) {
  const queryClient = useQueryClient();

  const query = useQuery<PriceHistoryEntry[], Error>({
    queryKey: [...PRICE_HISTORY_KEY, catalogItemId, filters],
    queryFn: () => priceHistoryApi.list(catalogItemId!, filters),
    enabled: !!catalogItemId,
  });

  const create = useMutation<PriceHistoryEntry, Error, PriceHistoryCreate>({
    mutationFn: (data) => priceHistoryApi.create(catalogItemId!, data),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: [...PRICE_HISTORY_KEY, catalogItemId],
      }),
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (id) => priceHistoryApi.remove(id),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: [...PRICE_HISTORY_KEY, catalogItemId],
      }),
  });

  return { ...query, create, remove };
}

export function useLatestPrices(catalogItemId: string | undefined) {
  return useQuery<LatestPriceEntry[], Error>({
    queryKey: [...PRICE_HISTORY_KEY, catalogItemId, "latest"],
    queryFn: () => priceHistoryApi.latest(catalogItemId!),
    enabled: !!catalogItemId,
  });
}

export function useRefreshMarketValue(collectionItemId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation<ValueUpdateResult, Error, void>({
    mutationFn: () => priceHistoryApi.refreshValue(collectionItemId!),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["collection-items", collectionItemId],
      });
      queryClient.invalidateQueries({ queryKey: ["collection-stats"] });
    },
  });
}
