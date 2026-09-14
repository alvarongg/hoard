import { useRef } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../ui/Button";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { ErrorMessage } from "../ui/ErrorMessage";
import { ImportPreviewTable } from "./ImportPreviewTable";
import { ImportReport } from "./ImportReport";
import { useJsonImport } from "../../hooks/useTransfer";

export function ImportWizard() {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const {
    step,
    preview,
    report,
    selectFile,
    confirm,
    cancel,
    isPreviewing,
    isExecuting,
    error,
  } = useJsonImport();

  return (
    <div>
      <ol className="mb-4 flex gap-2 text-sm" aria-label={t("import.steps.label")}>
        {(["upload", "preview", "confirm", "report"] as const).map((s) => (
          <li
            key={s}
            aria-current={step === s ? "step" : undefined}
            className={
              step === s
                ? "font-semibold text-blue-600"
                : "text-gray-500 dark:text-gray-400"
            }
          >
            {t(`import.steps.${s}`)}
          </li>
        ))}
      </ol>

      {error && <ErrorMessage message={error.message} />}

      {step === "upload" && (
        <div>
          <input
            ref={inputRef}
            type="file"
            accept="application/json"
            aria-label={t("import.selectFile")}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) selectFile(f);
            }}
          />
          {isPreviewing && <LoadingSpinner />}
        </div>
      )}

      {step === "preview" && preview && (
        <div>
          <ImportPreviewTable changes={preview.changes} />
          <div className="mt-4 flex gap-2">
            <Button onClick={confirm} disabled={isExecuting}>
              {t("import.confirm")}
            </Button>
            <Button variant="secondary" onClick={cancel}>
              {t("import.cancel")}
            </Button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            {t("import.cancelHint")}
          </p>
          {isExecuting && <LoadingSpinner />}
        </div>
      )}

      {step === "report" && report && (
        <div>
          <ImportReport report={report} />
          <Button className="mt-4" variant="secondary" onClick={cancel}>
            {t("import.done")}
          </Button>
        </div>
      )}
    </div>
  );
}
