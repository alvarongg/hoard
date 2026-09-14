import { fetchApi } from "./api";
import type {
  CatalogLoadResult,
  CatalogManifest,
} from "../types/catalogLibrary";

export const catalogLibraryApi = {
  manifest: (): Promise<CatalogManifest> =>
    fetchApi<CatalogManifest>("/catalog-library/manifest"),

  preview: (catalogId: string): Promise<CatalogLoadResult> =>
    fetchApi<CatalogLoadResult>("/catalog-library/preview", {
      method: "POST",
      body: JSON.stringify({ catalog_id: catalogId }),
    }),

  load: (catalogId: string): Promise<CatalogLoadResult> =>
    fetchApi<CatalogLoadResult>("/catalog-library/load", {
      method: "POST",
      body: JSON.stringify({ catalog_id: catalogId }),
    }),

  importFile: (file: File): Promise<CatalogLoadResult> => {
    const form = new FormData();
    form.append("file", file);
    return fetchApi<CatalogLoadResult>("/catalog-import/execute", {
      method: "POST",
      body: form,
    });
  },
};
