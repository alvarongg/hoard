import { useState } from "react";
import { useTranslation } from "react-i18next";
import { catalogLibraryApi } from "../services/catalogLibraryApi";
import type { CatalogLoadResult } from "../types/catalogLibrary";

export function CatalogImportPage() {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CatalogLoadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await catalogLibraryApi.importFile(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main>
      <h1 className="text-2xl font-bold text-content">
        {t("settings.importCatalog")}
      </h1>
      <p className="mt-1 text-content-muted">
        {t("catalogImport.description")}
      </p>
      <form onSubmit={handleSubmit} className="mt-4 max-w-xl space-y-3">
        <label className="block text-sm font-medium text-content">
          {t("catalogImport.selectFile")}
          <input
            type="file"
            accept="application/json,.json"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block w-full text-sm"
          />
        </label>
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? t("catalogLibrary.loading") : t("common.create")}
        </button>
      </form>
      {result && (
        <p role="status" className="mt-3 text-sm text-green-700">
          {t("catalogLibrary.loaded", {
            created: result.createdCount,
            updated: result.updatedCount,
            skipped: result.skippedCount,
          })}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </main>
  );
}
