import { useQuery } from "@tanstack/react-query";
import { catalogsApi } from "../services/catalogsApi";
import type { CatalogItem } from "../types/item";

export function useCatalogItems(catalogId: string) {
  const query = useQuery<CatalogItem[], Error>({
    queryKey: ["catalogs", catalogId, "items"],
    queryFn: () => catalogsApi.listItems(catalogId),
    enabled: !!catalogId,
  });

  return query;
}
