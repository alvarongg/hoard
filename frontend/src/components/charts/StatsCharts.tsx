import { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import { ChartContainer } from "./ChartContainer";
import {
  useValuationStats,
  useCategoryStats,
  useTimelineStats,
} from "../../hooks/useStats";
import type { ChartSeries } from "../../types/chart";

// Recharts is loaded lazily so pages that don't render charts stay light.
const RechartsBars = lazy(() => import("./RechartsBars"));
const RechartsArea = lazy(() => import("./RechartsArea"));

function ChartVisual({ series }: { series: ChartSeries[] }) {
  return (
    <Suspense fallback={null}>
      <RechartsBars series={series} />
    </Suspense>
  );
}

export function InvestmentVsValueChart() {
  const { t } = useTranslation();
  const valuation = useValuationStats();

  const series: ChartSeries[] = valuation.data
    ? [
        {
          key: "amounts",
          label: t("charts.investmentVsValue"),
          marker: "square",
          points: [
            {
              label: t("stats.totalInvested"),
              value: Number(valuation.data.totalInvested),
            },
            {
              label: t("stats.totalValue"),
              value: Number(valuation.data.currentValue),
            },
          ],
        },
      ]
    : [];

  return (
    <ChartContainer
      title={t("charts.investmentVsValue")}
      description={t("charts.descriptions.investmentVsValue")}
      data={series}
      isLoading={valuation.isLoading}
      error={valuation.error}
      onRetry={() => valuation.refetch()}
    >
      <ChartVisual series={series} />
    </ChartContainer>
  );
}

export function CategoryDistributionChart() {
  const { t } = useTranslation();
  const categories = useCategoryStats();

  const series: ChartSeries[] = categories.data
    ? [
        {
          key: "value",
          label: t("charts.categoryDistribution"),
          marker: "triangle",
          points: categories.data.map((c) => ({
            label: c.subCategoryName,
            value: Number(c.currentValue),
          })),
        },
      ]
    : [];

  return (
    <ChartContainer
      title={t("charts.categoryDistribution")}
      description={t("charts.descriptions.categoryDistribution")}
      data={series}
      isLoading={categories.isLoading}
      error={categories.error}
      onRetry={() => categories.refetch()}
    >
      <ChartVisual series={series} />
    </ChartContainer>
  );
}

export function ValuationOverTimeChart() {
  const { t } = useTranslation();
  const timeline = useTimelineStats("month");

  const series: ChartSeries[] = timeline.data
    ? [
        {
          key: "invested",
          label: t("charts.valuationOverTime"),
          marker: "circle",
          points: timeline.data.map((e) => ({
            label: e.period,
            value: Number(e.invested),
          })),
        },
      ]
    : [];

  return (
    <ChartContainer
      title={t("charts.valuationOverTime")}
      description={t("charts.descriptions.valuationOverTime")}
      data={series}
      isLoading={timeline.isLoading}
      error={timeline.error}
      onRetry={() => timeline.refetch()}
    >
      <Suspense fallback={null}>
        <RechartsArea series={series} />
      </Suspense>
    </ChartContainer>
  );
}

export function AcquisitionTimelineChart() {
  const { t } = useTranslation();
  const timeline = useTimelineStats("month");

  const series: ChartSeries[] = timeline.data
    ? [
        {
          key: "count",
          label: t("charts.acquisitionTimeline"),
          marker: "diamond",
          points: timeline.data.map((e) => ({
            label: e.period,
            value: e.itemCount,
          })),
        },
      ]
    : [];

  return (
    <ChartContainer
      title={t("charts.acquisitionTimeline")}
      description={t("charts.descriptions.acquisitionTimeline")}
      data={series}
      isLoading={timeline.isLoading}
      error={timeline.error}
      onRetry={() => timeline.refetch()}
    >
      <Suspense fallback={null}>
        <RechartsArea series={series} />
      </Suspense>
    </ChartContainer>
  );
}
