import { useTranslation } from "react-i18next";
import type { BatchImportResult } from "../../types/transfer";

interface ImportReportProps {
  report: BatchImportResult;
}

export function ImportReport({ report }: ImportReportProps) {
  const { t } = useTranslation();
  return (
    <section aria-labelledby="import-report-heading">
      <h3
        id="import-report-heading"
        className="mb-2 text-sm font-semibold text-gray-900 dark:text-white"
      >
        {t("import.report")}
      </h3>
      <ul className="text-sm text-gray-700 dark:text-gray-300">
        <li>
          {t("import.toCreate")}: {report.createdCount}
        </li>
        <li>
          {t("import.toUpdate")}: {report.updatedCount}
        </li>
        <li>
          {t("import.toSkip")}: {report.skippedCount}
        </li>
      </ul>
      {report.errors.length > 0 && (
        <div className="mt-2">
          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            {t("import.partialErrors")}
          </p>
          <ul className="text-sm text-red-600 dark:text-red-400" role="list">
            {report.errors.map((e, i) => (
              <li key={i}>
                {t("import.errorRow", { row: e.row })}: {e.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
