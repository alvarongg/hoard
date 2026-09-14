import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchApi, toSnakeCase } from "../services/api";
import type { CatalogItem } from "../types/item";

export interface CatalogItemUpdate {
  title?: string;
  subtitle?: string | null;
  description?: string | null;
  region?: string | null;
  manufacturer?: string | null;
  publisher?: string | null;
  developer?: string | null;
  variation?: string | null;
  variationDetails?: string | null;
  relatedItemsGroup?: string | null;
  customFields?: Record<string, unknown>;
}

export function useUpdateCatalogItem(itemId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CatalogItemUpdate) =>
      fetchApi<CatalogItem>(`/catalog-items/${itemId}`, {
        method: "PUT",
        body: JSON.stringify(toSnakeCase(data)),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["catalog-item", itemId] });
      void qc.invalidateQueries({ queryKey: ["catalogs"] });
    },
  });
}
