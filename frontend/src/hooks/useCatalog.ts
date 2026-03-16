import { useQuery } from "@tanstack/react-query";
import { catalogsApi } from "../services/catalogsApi";
import type { Catalog } from "../types/catalog";

export function useCatalog(id: string) {
  const query = useQuery<Catalog, Error>({
    queryKey: ["catalogs", id],
    queryFn: () => catalogsApi.getById(id),
    enabled: !!id,
  });

  return query;
}
