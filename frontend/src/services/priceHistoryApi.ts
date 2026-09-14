import { fetchApi, toSnakeCase } from "./api";
import type {
  PriceHistoryEntry,
  PriceHistoryCreate,
  PriceHistoryFilters,
  LatestPriceEntry,
  ValueUpdateResult,
} from "../types/priceHistory";

export const priceHistoryApi = {
  list: (
    catalogItemId: string,
    filters?: PriceHistoryFilters,
  ): Promise<PriceHistoryEntry[]> => {
    const params = new URLSearchParams();
    if (filters) {
      const snakeFilters = toSnakeCase<Record<string, unknown>>(filters);
      for (const [key, value] of Object.entries(snakeFilters)) {
        if (value !== undefined && value !== null && value !== "") {
          params.append(key, String(value));
        }
      }
    }
    const qs = params.toString();
    const endpoint = qs
      ? `/catalog-items/${catalogItemId}/price-history?${qs}`
      : `/catalog-items/${catalogItemId}/price-history`;
    return fetchApi<PriceHistoryEntry[]>(endpoint);
  },

  create: (
    catalogItemId: string,
    data: PriceHistoryCreate,
  ): Promise<PriceHistoryEntry> =>
    fetchApi<PriceHistoryEntry>(
      `/catalog-items/${catalogItemId}/price-history`,
      {
        method: "POST",
        body: JSON.stringify(toSnakeCase(data)),
      },
    ),

  remove: (priceHistoryId: string): Promise<void> =>
    fetchApi<void>(`/price-history/${priceHistoryId}`, { method: "DELETE" }),

  latest: (catalogItemId: string): Promise<LatestPriceEntry[]> =>
    fetchApi<LatestPriceEntry[]>(
      `/catalog-items/${catalogItemId}/price-history/latest`,
    ),

  refreshValue: (collectionItemId: string): Promise<ValueUpdateResult> =>
    fetchApi<ValueUpdateResult>(
      `/collection-items/${collectionItemId}/refresh-value`,
      { method: "POST" },
    ),
};
