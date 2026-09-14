import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import { useCatalog } from "../hooks/useCatalog";
import { useCatalogItems } from "../hooks/useCatalogItems";
import { usePriceHistory, useLatestPrices } from "../hooks/usePriceHistory";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { PriceHistoryTable } from "../components/priceHistory/PriceHistoryTable";
import { PriceHistoryForm } from "../components/priceHistory/PriceHistoryForm";
import { LatestPriceSummary } from "../components/priceHistory/LatestPriceSummary";

export function CatalogDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const catalog = useCatalog(id ?? "");
  const catalogItems = useCatalogItems(id ?? "");
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  if (catalog.isLoading) {
    return (
      <main>
        <LoadingSpinner />
      </main>
    );
  }

  if (catalog.error) {
    return (
      <main>
        <ErrorMessage
          message={t("errors.loadFailed")}
          onRetry={() => catalog.refetch()}
        />
      </main>
    );
  }

  if (!catalog.data) {
    return (
      <main>
        <ErrorMessage message={t("errors.notFound")} />
      </main>
    );
  }

  return (
    <main>
      <button
        onClick={() => navigate("/catalogs")}
        className="text-sm text-blue-600 hover:underline"
        aria-label={t("navigation.catalogs")}
      >
        ← {t("navigation.catalogs")}
      </button>
      <h1 className="mt-1 text-2xl font-bold text-gray-900">
        {catalog.data.name}
      </h1>
      {catalog.data.description && (
        <p className="mt-1 text-gray-600">{catalog.data.description}</p>
      )}

      <section aria-label={t("catalogs.items")} className="mt-6">
        <h2 className="text-lg font-semibold text-gray-900">
          {t("catalogs.items")}
        </h2>

        <div className="mt-3">
          {catalogItems.isLoading && <LoadingSpinner />}

          {catalogItems.error && (
            <ErrorMessage
              message={t("errors.loadFailed")}
              onRetry={() => catalogItems.refetch()}
            />
          )}

          {!catalogItems.isLoading && !catalogItems.error && (
            <>
              {(catalogItems.data?.length ?? 0) === 0 ? (
                <EmptyState title={t("items.empty")} />
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {catalogItems.data?.map((item) => (
                    <Card key={item.id} title={item.title}>
                      {item.description && (
                        <p className="text-sm text-gray-600">
                          {item.description}
                        </p>
                      )}
                      {item.manufacturer && (
                        <p className="mt-1 text-sm text-gray-500">
                          {item.manufacturer}
                        </p>
                      )}
                      <Button
                        variant="secondary"
                        className="mt-2"
                        onClick={() =>
                          setSelectedItemId(
                            selectedItemId === item.id ? null : item.id,
                          )
                        }
                        aria-expanded={selectedItemId === item.id}
                      >
                        {t("priceHistory.title")}
                      </Button>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {selectedItemId && (
        <PriceHistorySection catalogItemId={selectedItemId} />
      )}
    </main>
  );
}

interface PriceHistorySectionProps {
  catalogItemId: string;
}

function PriceHistorySection({ catalogItemId }: PriceHistorySectionProps) {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch, create, remove } =
    usePriceHistory(catalogItemId);
  const latest = useLatestPrices(catalogItemId);
  const [showForm, setShowForm] = useState(false);

  return (
    <section aria-label={t("priceHistory.title")} className="mt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t("priceHistory.title")}
        </h2>
        <Button onClick={() => setShowForm((s) => !s)}>
          {t("priceHistory.add")}
        </Button>
      </div>

      {showForm && (
        <div className="mt-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <PriceHistoryForm
            isLoading={create.isPending}
            onCancel={() => setShowForm(false)}
            onSubmit={(payload) =>
              create.mutate(payload, { onSuccess: () => setShowForm(false) })
            }
          />
        </div>
      )}

      {latest.data && latest.data.length > 0 && (
        <div className="mt-4">
          <LatestPriceSummary entries={latest.data} />
        </div>
      )}

      <div className="mt-4">
        {isLoading && <LoadingSpinner />}
        {error && (
          <ErrorMessage
            message={t("errors.loadFailed")}
            onRetry={() => refetch()}
          />
        )}
        {!isLoading && !error && (
          <PriceHistoryTable
            entries={data ?? []}
            onDelete={(entryId) => remove.mutate(entryId)}
          />
        )}
      </div>
    </section>
  );
}
