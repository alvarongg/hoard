import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useCatalogs } from "../hooks/useCatalogs";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";

export function CatalogsPage() {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch } = useCatalogs();
  const [searchTerm, setSearchTerm] = useState("");

  if (isLoading) {
    return (
      <main>
        <h1 className="text-2xl font-bold text-gray-900">
          {t("catalogs.title")}
        </h1>
        <LoadingSpinner />
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <h1 className="text-2xl font-bold text-gray-900">
          {t("catalogs.title")}
        </h1>
        <ErrorMessage
          message={t("errors.loadFailed")}
          onRetry={() => refetch()}
        />
      </main>
    );
  }

  const filtered = data?.filter((catalog) =>
    catalog.name.toLowerCase().includes(searchTerm.toLowerCase()),
  ) ?? [];

  return (
    <main>
      <h1 className="text-2xl font-bold text-gray-900">
        {t("catalogs.title")}
      </h1>

      <div className="mt-4">
        <Input
          label={t("common.search")}
          placeholder={t("catalogs.search")}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          aria-label={t("catalogs.search")}
        />
      </div>

      <div className="mt-6">
        {filtered.length === 0 ? (
          <EmptyState
            title={searchTerm ? t("common.noResults") : t("catalogs.empty")}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((catalog) => (
              <Link
                key={catalog.id}
                to={`/catalogs/${catalog.id}`}
                aria-label={catalog.name}
              >
                <Card>
                  <h2 className="mb-2 text-lg font-semibold text-gray-900">
                    {catalog.name}
                  </h2>
                  {catalog.description && (
                    <p className="text-sm text-gray-600">
                      {catalog.description}
                    </p>
                  )}
                  <p className="mt-2 text-sm text-gray-500">
                    {t("collections.itemCount", { count: catalog.totalItems })}
                  </p>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
