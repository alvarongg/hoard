import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { ErrorMessage } from "../ui/ErrorMessage";
import { EmptyState } from "../ui/EmptyState";
import { ChartDataTable } from "./ChartDataTable";
import type { ChartSeries } from "../../types/chart";

interface ChartContainerProps {
  title: string;
  description: string;
  data: ChartSeries[];
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  children?: ReactNode;
}

/**
 * ChartContainer - accessible wrapper for a chart.
 *
 * Renders a <figure> with <figcaption>; the visual chart (children) is
 * marked aria-hidden, and an equivalent ChartDataTable is exposed inside a
 * <details> disclosure that is reachable by keyboard.
 */
export function ChartContainer({
  title,
  description,
  data,
  isLoading = false,
  error = null,
  onRetry,
  children,
}: ChartContainerProps) {
  const { t } = useTranslation();

  const isEmpty = data.length === 0 || data.every((s) => s.points.length === 0);

  return (
    <figure className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
      <figcaption className="mb-2">
        <span className="block text-base font-semibold text-gray-900 dark:text-white">
          {title}
        </span>
        <span className="block text-sm text-gray-500 dark:text-gray-400">
          {description}
        </span>
      </figcaption>

      {isLoading && <LoadingSpinner />}
      {error && (
        <ErrorMessage
          message={t("charts.loadError")}
          onRetry={onRetry}
        />
      )}

      {!isLoading && !error && isEmpty && (
        <EmptyState title={t("charts.noData")} />
      )}

      {!isLoading && !error && !isEmpty && (
        <>
          <div aria-hidden="true">{children}</div>
          <details className="mt-3">
            <summary className="cursor-pointer text-sm text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500">
              {t("charts.viewDataTable")}
            </summary>
            <div className="mt-2">
              <ChartDataTable caption={title} series={data} />
            </div>
          </details>
        </>
      )}
    </figure>
  );
}
