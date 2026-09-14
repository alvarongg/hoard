export type ExportFormat = "json" | "csv";

export interface ImportEntityChange {
  entityType: string;
  identifier: string;
  action: "create" | "update" | "skip";
  reason: string | null;
}

export interface ImportPreview {
  schemaVersion: string;
  toCreate: number;
  toUpdate: number;
  toSkip: number;
  changes: ImportEntityChange[];
  errors: Array<{
    entityType: string;
    identifier: string;
    message: string;
  }>;
}

export interface BatchImportResult {
  createdCount: number;
  errorCount: number;
  updatedCount: number;
  skippedCount: number;
  errors: Array<{ row: number; message: string }>;
}
