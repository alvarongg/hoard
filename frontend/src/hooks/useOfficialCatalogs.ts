import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { catalogLibraryApi } from "../services/catalogLibraryApi";
import type {
  CatalogLoadResult,
  CatalogManifest,
} from "../types/catalogLibrary";

const MANIFEST_KEY = ["catalog-library", "manifest"] as const;

export function useOfficialCatalogs() {
  const queryClient = useQueryClient();

  const query = useQuery<CatalogManifest, Error>({
    queryKey: MANIFEST_KEY,
    queryFn: () => catalogLibraryApi.manifest(),
  });

  const load = useMutation<CatalogLoadResult, Error, string>({
    mutationFn: (catalogId) => catalogLibraryApi.load(catalogId),
    onSuccess: () => {
      // Loading a catalog creates catalogs/items; refresh those views.
      void queryClient.invalidateQueries({ queryKey: ["catalogs"] });
    },
  });

  return { ...query, load };
}
