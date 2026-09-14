import { useMutation, useQueryClient } from "@tanstack/react-query";
import { catalogsApi } from "../services/catalogsApi";
import type { CatalogItem, CatalogItemCreate } from "../types/item";

export function useCreateCatalogItem(catalogId: string) {
  const queryClient = useQueryClient();

  return useMutation<CatalogItem, Error, CatalogItemCreate>({
    mutationFn: (data) => catalogsApi.createItem(catalogId, data),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["catalogs", catalogId, "items"],
      }),
  });
}
