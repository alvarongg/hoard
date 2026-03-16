import { useQuery } from "@tanstack/react-query";
import { collectionsApi } from "../services/collectionsApi";
import type { Collection } from "../types/collection";

export function useCollection(id: string) {
  const query = useQuery<Collection, Error>({
    queryKey: ["collections", id],
    queryFn: () => collectionsApi.getById(id),
    enabled: !!id,
  });

  return query;
}
