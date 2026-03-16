import { useQuery } from "@tanstack/react-query";
import { catalogsApi } from "../services/catalogsApi";
import type { Catalog } from "../types/catalog";
import type { CatalogItem } from "../types/item";

const CATALOGS_KEY = ["catalogs"] as const;

export function useCatalogs() {
  const query = useQuery<Catalog[], Error>({
    queryKey: CATALOGS_KEY,
    queryFn: () => catalogsApi.list(),
  });

  return query;
}

export function useCatalogSearch(searchQuery: string) {
  const query = useQuery<CatalogItem[], Error>({
    queryKey: ["catalog-items", "search", searchQuery],
    queryFn: () => catalogsApi.searchItems(searchQuery),
    enabled: searchQuery.length > 0,
  });

  return query;
}
