import { API_BASE_URL, toCamelCase } from "./api";
import type {
  ExportFormat,
  ImportPreview,
  BatchImportResult,
} from "../types/transfer";

async function download(endpoint: string, filename: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`Export failed: ${response.status}`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const exportApi = {
  collection: (id: string): Promise<void> =>
    download(`/export/collections/${id}`, `collection-${id}.json`),

  catalog: (id: string, format: ExportFormat = "json"): Promise<void> =>
    download(`/export/catalogs/${id}?format=${format}`, `catalog-${id}.${format}`),

  wishlist: (): Promise<void> =>
    download("/export/wishlist", "wishlist.json"),
};

async function upload<T>(endpoint: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: form,
  });
  const data: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `Import failed: ${response.status}`;
    throw new Error(detail);
  }
  return toCamelCase<T>(data);
}

export const importApi = {
  preview: (file: File): Promise<ImportPreview> =>
    upload<ImportPreview>("/import/preview", file),

  execute: (file: File): Promise<BatchImportResult> =>
    upload<BatchImportResult>("/import/execute", file),
};
