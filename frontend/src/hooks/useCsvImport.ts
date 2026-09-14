import { useMutation, useQueryClient } from "@tanstack/react-query";
import { catalogsApi } from "../services/catalogsApi";
import type { BatchImportResult } from "../types/catalog";

export function useCsvImport(catalogId: string) {
  const queryClient = useQueryClient();

  return useMutation<BatchImportResult, Error, File>({
    mutationFn: (file) => catalogsApi.importCsv(catalogId, file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["catalogs", catalogId, "items"],
      });
      // Prefix key: refreshes the catalog detail and the list so total_items updates.
      await queryClient.invalidateQueries({ queryKey: ["catalogs"] });
    },
  });
}
