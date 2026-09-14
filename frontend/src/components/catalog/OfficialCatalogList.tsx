import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOfficialCatalogs } from "../../hooks/useOfficialCatalogs";
import type { CatalogLoadResult } from "../../types/catalogLibrary";

export function OfficialCatalogList() {
  const { t } = useTranslation();
  const { data, isLoading, isError, load } = useOfficialCatalogs();
  const [result, setResult] = useState<CatalogLoadResult | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleLoad = (catalogId: string): void => {
    setResult(null);
    setLoadingId(catalogId);
    load.mutate(catalogId, {
      onSuccess: (res) => setResult(res),
      onSettled: () => setLoadingId(null),
    });
  };

  if (isLoading) {
    return <p role="status">{t("common.loading")}</p>;
  }
  if (isError) {
    return (
      <p role="alert" className="text-red-600">
        {t("catalogLibrary.loadError")}
      </p>
    );
  }

  const catalogs = data?.catalogs ?? [];
  if (catalogs.length === 0) {
    return <p>{t("catalogLibrary.empty")}</p>;
  }

  return (
    <div>
      {result && (
        <p role="status" className="mb-3 text-sm text-green-700">
          {t("catalogLibrary.loaded", {
            created: result.createdCount,
            updated: result.updatedCount,
            skipped: result.skippedCount,
          })}
        </p>
      )}
      {load.isError && (
        <p role="alert" className="mb-3 text-sm text-red-600">
          {t("catalogLibrary.loadError")}
        </p>
      )}
      <ul className="space-y-3">
        {catalogs.map((c) => (
          <li
            key={c.id}
            className="flex items-center justify-between rounded-lg border border-border p-3"
          >
            <div>
              <p className="font-medium text-content">{c.name}</p>
              <p className="text-sm text-content-muted">
                {c.system} · v{c.version} · {c.itemCount ?? 0}{" "}
                {t("catalogLibrary.items")}
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleLoad(c.id)}
              disabled={loadingId === c.id}
              className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {loadingId === c.id
                ? t("catalogLibrary.loading")
                : t("catalogLibrary.load")}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
