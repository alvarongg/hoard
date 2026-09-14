export interface CatalogManifestEntry {
  id: string;
  name: string;
  description?: string | null;
  system?: string | null;
  version?: string | null;
  itemCount?: number;
  updatedAt?: string;
  path: string;
  checksum?: string;
}

export interface CatalogManifest {
  schemaVersion: string;
  generatedAt?: string;
  catalogs: CatalogManifestEntry[];
}

export interface CatalogLoadResult {
  createdCount: number;
  updatedCount: number;
  skippedCount: number;
  errorCount: number;
}
