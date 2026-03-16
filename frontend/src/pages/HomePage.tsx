import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useCollections } from "../hooks/useCollections";
import { useCatalogs } from "../hooks/useCatalogs";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Card } from "../components/ui/Card";

export function HomePage() {
  const { t } = useTranslation();
  const collections = useCollections();
  const catalogs = useCatalogs();

  const isLoading = collections.isLoading || catalogs.isLoading;
  const error = collections.error || catalogs.error;

  if (isLoading) {
    return (
      <main>
        <LoadingSpinner />
      </main>
    );
  }

  if (error) {
    return (
      <main>
        <ErrorMessage
          message={t("errors.loadFailed")}
          onRetry={() => {
            collections.refetch();
            catalogs.refetch();
          }}
        />
      </main>
    );
  }

  const collectionCount = collections.data?.length ?? 0;
  const catalogCount = catalogs.data?.length ?? 0;

  return (
    <main>
      <h1 className="text-2xl font-bold text-gray-900">
        {t("home.welcome")}
      </h1>
      <p className="mt-1 text-gray-600">{t("home.description")}</p>

      <section aria-label={t("home.quickAccess")} className="mt-6">
        <h2 className="sr-only">{t("home.quickAccess")}</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              {t("home.totalCollections")}
            </h3>
            <p className="text-3xl font-bold text-blue-600">{collectionCount}</p>
            <Link
              to="/collections"
              className="mt-2 inline-block text-sm text-blue-600 underline hover:text-blue-800"
              aria-label={t("navigation.collections")}
            >
              {t("home.viewAll")}
            </Link>
          </Card>

          <Card>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              {t("home.totalCatalogs")}
            </h3>
            <p className="text-3xl font-bold text-blue-600">{catalogCount}</p>
            <Link
              to="/catalogs"
              className="mt-2 inline-block text-sm text-blue-600 underline hover:text-blue-800"
              aria-label={t("navigation.catalogs")}
            >
              {t("home.viewAll")}
            </Link>
          </Card>
        </div>
      </section>

      <section aria-label={t("home.recentCollections")} className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900">
          {t("home.recentCollections")}
        </h2>
        {collectionCount === 0 ? (
          <p className="mt-2 text-sm text-gray-500">{t("home.getStarted")}</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {collections.data?.slice(0, 5).map((col) => (
              <li key={col.id}>
                <Link
                  to={`/collections/${col.id}`}
                  className="block rounded-md border border-gray-200 p-3 hover:bg-gray-50"
                  aria-label={col.name}
                >
                  <span className="font-medium text-gray-900">{col.name}</span>
                  {col.description && (
                    <span className="ml-2 text-sm text-gray-500">
                      {col.description}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
