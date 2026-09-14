import { useQuery } from "@tanstack/react-query";

import { fetchApi } from "../services/api";
import type { CatalogItem } from "../types/item";

export function useCatalogItem(itemId: string | undefined) {
  return useQuery<CatalogItem, Error>({
    queryKey: ["catalog-item", itemId],
    queryFn: () => fetchApi<CatalogItem>(`/catalog-items/${itemId as string}`),
    enabled: Boolean(itemId),
  });
}
