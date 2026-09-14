import { useTranslation } from "react-i18next";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/stats/MetricCard";
import { CollectionStatsTable } from "../components/stats/CollectionStatsTable";
import { CategoryStatsTable } from "../components/stats/CategoryStatsTable";
import {
  InvestmentVsValueChart,
  CategoryDistributionChart,
  ValuationOverTimeChart,
  AcquisitionTimelineChart,
} from "../components/charts/StatsCharts";
import {
  useDashboardStats,
  useCollectionStatsList,
  useCategoryStats,
} from "../hooks/useStats";

export function StatsPage() {
  const { t } = useTranslation();
  const dashboard = useDashboardStats();
  const collections = useCollectionStatsList();
  const categories = useCategoryStats();

  const globalEmpty =
    dashboard.data?.totalItems === 0 &&
    dashboard.data?.totalCollections === 0;

  return (
    <main>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("stats.title")}
      </h1>

      {/* Dashboard metrics */}
      <section aria-label={t("stats.title")} className="mt-4">
        {dashboard.isLoading && <LoadingSpinner />}
        {dashboard.isError && (
          <ErrorMessage
            message={t("errors.loadFailed")}
            onRetry={() => dashboard.refetch()}
          />
        )}
        {dashboard.data && !globalEmpty && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label={t("stats.totalItems")}
              value={String(dashboard.data.totalItems)}
            />
            <MetricCard
              label={t("stats.totalValue")}
              value={dashboard.data.currentValue}
            />
            <MetricCard
              label={t("stats.totalInvested")}
              value={dashboard.data.totalInvested}
            />
            <MetricCard
              label={t("stats.roi")}
              value={
                dashboard.data.roiPercentage === null
                  ? t("stats.roiUnavailable")
                  : `${dashboard.data.roiPercentage}%`
              }
            />
          </div>
        )}
        {dashboard.data && globalEmpty && (
          <EmptyState title={t("stats.empty")} />
        )}
      </section>

      {/* By collection */}
      {!globalEmpty && (
        <section aria-label={t("stats.byCollection")} className="mt-8">
          <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
            {t("stats.byCollection")}
          </h2>
          {collections.isLoading && <LoadingSpinner />}
          {collections.isError && (
            <ErrorMessage
              message={t("errors.loadFailed")}
              onRetry={() => collections.refetch()}
            />
          )}
          {collections.data && (
            <CollectionStatsTable entries={collections.data} />
          )}
        </section>
      )}

      {/* By category */}
      {!globalEmpty && (
        <section aria-label={t("stats.byCategory")} className="mt-8">
          <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
            {t("stats.byCategory")}
          </h2>
          {categories.isLoading && <LoadingSpinner />}
          {categories.isError && (
            <ErrorMessage
              message={t("errors.loadFailed")}
              onRetry={() => categories.refetch()}
            />
          )}
          {categories.data && (
            <CategoryStatsTable entries={categories.data} />
          )}
        </section>
      )}

      {!globalEmpty && (
        <section aria-label={t("stats.timeline")} className="mt-8">
          <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
            {t("stats.timeline")}
          </h2>
          <div className="grid gap-4 lg:grid-cols-2">
            <InvestmentVsValueChart />
            <CategoryDistributionChart />
            <ValuationOverTimeChart />
            <AcquisitionTimelineChart />
          </div>
        </section>
      )}
    </main>
  );
}
