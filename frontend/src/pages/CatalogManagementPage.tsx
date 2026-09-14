import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { CsvUploadForm } from "../components/catalogs/CsvUploadForm";
import { InlineCatalogItemForm } from "../components/items/InlineCatalogItemForm";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { Select } from "../components/ui/Select";
import { useCatalogItems } from "../hooks/useCatalogItems";
import { useCatalogs } from "../hooks/useCatalogs";

const PAGE_SIZE = 20;

type ActivePanel = "none" | "createItem" | "importCsv";

export function CatalogManagementPage() {
  const { t } = useTranslation();
  const catalogs = useCatalogs();

  const [selectedCatalogId, setSelectedCatalogId] = useState("");
  const [activePanel, setActivePanel] = useState<ActivePanel>("none");
  const [page, setPage] = useState(0);

  const items = useCatalogItems(selectedCatalogId);

  const firstCatalogId = catalogs.data?.[0]?.id ?? "";

  useEffect(() => {
    if (!firstCatalogId) return;
    setSelectedCatalogId((current) => current || firstCatalogId);
  }, [firstCatalogId]);

  function handleCatalogChange(catalogId: string) {
    setSelectedCatalogId(catalogId);
    setActivePanel("none");
    setPage(0);
  }

  if (catalogs.isLoading) {
    return (
      <main>
        <PageHeading title={t("catalogs.management.title")} />
        <LoadingSpinner />
      </main>
    );
  }

  if (catalogs.error) {
    return (
      <main>
        <PageHeading title={t("catalogs.management.title")} />
        <ErrorMessage
          message={t("errors.loadFailed")}
          onRetry={() => catalogs.refetch()}
        />
      </main>
    );
  }

  const availableCatalogs = catalogs.data ?? [];

  if (availableCatalogs.length === 0) {
    return (
      <main>
        <PageHeading title={t("catalogs.management.title")} />
        <EmptyState title={t("catalogs.management.noCatalogs")} />
      </main>
    );
  }

  const allItems = items.data ?? [];
  const totalPages = Math.max(1, Math.ceil(allItems.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);
  const visibleItems = allItems.slice(
    currentPage * PAGE_SIZE,
    currentPage * PAGE_SIZE + PAGE_SIZE,
  );

  return (
    <main>
      <PageHeading title={t("catalogs.management.title")} />

      <div className="mt-4 max-w-sm">
        <Select
          label={t("catalogs.management.selectCatalog")}
          value={selectedCatalogId}
          onChange={(event) => handleCatalogChange(event.target.value)}
          options={availableCatalogs.map((catalog) => ({
            value: catalog.id,
            label: catalog.name,
          }))}
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={() => setActivePanel("createItem")}
          disabled={activePanel === "createItem"}
        >
          {t("catalogs.management.addItem")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setActivePanel("importCsv")}
          disabled={activePanel === "importCsv"}
        >
          {t("catalogs.management.importCsv")}
        </Button>
      </div>

      {activePanel === "createItem" && (
        <div className="mt-4">
          <InlineCatalogItemForm
            catalogId={selectedCatalogId}
            isLoading={false}
            onCreated={() => setActivePanel("none")}
            onCancel={() => setActivePanel("none")}
          />
        </div>
      )}

      {activePanel === "importCsv" && (
        <div className="mt-4">
          <CsvUploadForm
            catalogId={selectedCatalogId}
            onImportComplete={() => setPage(0)}
            onCancel={() => setActivePanel("none")}
          />
        </div>
      )}

      <section aria-label={t("catalogs.items")} className="mt-6">
        <h2 className="text-lg font-semibold text-gray-900">
          {t("catalogs.items")}
        </h2>
        <p className="text-sm text-gray-500">
          {t("catalogs.management.itemCount", { count: allItems.length })}
        </p>

        <div className="mt-3">
          {items.isLoading && <LoadingSpinner />}

          {items.error && (
            <ErrorMessage
              message={t("errors.loadFailed")}
              onRetry={() => items.refetch()}
            />
          )}

          {!items.isLoading && !items.error && allItems.length === 0 && (
            <EmptyState title={t("catalogs.management.noItems")} />
          )}

          {!items.isLoading && !items.error && allItems.length > 0 && (
            <>
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {visibleItems.map((item) => (
                  <li key={item.id}>
                    <Card title={item.title}>
                      {item.subtitle && (
                        <p className="text-sm text-gray-600">{item.subtitle}</p>
                      )}
                      {item.manufacturer && (
                        <p className="mt-1 text-sm text-gray-500">
                          {item.manufacturer}
                        </p>
                      )}
                    </Card>
                  </li>
                ))}
              </ul>

              {totalPages > 1 && (
                <nav
                  aria-label={t("catalogs.management.pagination")}
                  className="mt-4 flex items-center gap-3"
                >
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setPage(currentPage - 1)}
                    disabled={currentPage === 0}
                  >
                    {t("catalogs.management.previousPage")}
                  </Button>
                  <p aria-live="polite" className="text-sm text-gray-600">
                    {t("catalogs.management.pageStatus", {
                      current: currentPage + 1,
                      total: totalPages,
                    })}
                  </p>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setPage(currentPage + 1)}
                    disabled={currentPage >= totalPages - 1}
                  >
                    {t("catalogs.management.nextPage")}
                  </Button>
                </nav>
              )}
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function PageHeading({ title }: { title: string }) {
  return <h1 className="text-2xl font-bold text-gray-900">{title}</h1>;
}
