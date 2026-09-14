import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCsvImport } from "../../hooks/useCsvImport";
import type { BatchImportResult } from "../../types/catalog";
import { Button } from "../ui/Button";
import { ErrorMessage } from "../ui/ErrorMessage";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_EXTENSION = ".csv";
const ALLOWED_TYPES = ["text/csv", "application/vnd.ms-excel", ""];

interface CsvUploadFormProps {
  catalogId: string;
  onImportComplete: (result: BatchImportResult) => void;
  onCancel: () => void;
}

function hasCsvExtension(fileName: string): boolean {
  return fileName.toLowerCase().endsWith(ALLOWED_EXTENSION);
}

function isCsvFile(file: File): boolean {
  return hasCsvExtension(file.name) && ALLOWED_TYPES.includes(file.type);
}

export function CsvUploadForm({
  catalogId,
  onImportComplete,
  onCancel,
}: CsvUploadFormProps) {
  const { t } = useTranslation();
  const headingId = useId();
  const fileInputId = useId();
  const fileErrorId = useId();

  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string>();
  const [result, setResult] = useState<BatchImportResult>();

  const { mutate, isPending, error, reset } = useCsvImport(catalogId);

  function validateFile(candidate: File): string | undefined {
    if (!isCsvFile(candidate)) return t("catalogs.csv.invalidFileType");
    if (candidate.size > MAX_FILE_SIZE) return t("catalogs.csv.fileTooLarge");
    return undefined;
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    reset();
    setResult(undefined);

    const selected = event.target.files?.[0];
    if (!selected) {
      setFile(null);
      setFileError(undefined);
      return;
    }

    const validationError = validateFile(selected);
    setFileError(validationError);
    setFile(validationError ? null : selected);
  }

  function handleUpload() {
    if (!file) return;

    mutate(file, {
      onSuccess: (importResult) => {
        setResult(importResult);
        onImportComplete(importResult);
      },
    });
  }

  const isEmptyResult =
    result !== undefined &&
    result.createdCount === 0 &&
    result.errorCount === 0;

  return (
    <section
      aria-labelledby={headingId}
      className="space-y-4 rounded-md border border-gray-200 bg-gray-50 p-4"
    >
      <h3 id={headingId} className="text-sm font-semibold text-gray-800">
        {t("catalogs.csv.upload")}
      </h3>

      <div className="space-y-1">
        <label
          htmlFor={fileInputId}
          className="block text-sm font-medium text-gray-700"
        >
          {t("catalogs.csv.selectFile")}
        </label>
        <input
          id={fileInputId}
          type="file"
          accept={ALLOWED_EXTENSION}
          onChange={handleFileChange}
          disabled={isPending}
          aria-invalid={fileError ? true : undefined}
          aria-describedby={fileError ? fileErrorId : undefined}
          className="block w-full rounded-md border border-gray-300 p-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        />
        {fileError && (
          <p id={fileErrorId} role="alert" className="text-sm text-red-600">
            {fileError}
          </p>
        )}
      </div>

      <div aria-live="polite" className="space-y-3">
        {isPending && (
          <p className="text-sm text-gray-600">{t("catalogs.csv.importing")}</p>
        )}

        {result && !isPending && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-800">
              {t("catalogs.csv.importComplete")}
            </p>
            {isEmptyResult ? (
              <p className="text-sm text-gray-600">
                {t("catalogs.csv.noData")}
              </p>
            ) : (
              <ul className="text-sm text-gray-700">
                <li>
                  {t("catalogs.csv.createdCount", {
                    count: result.createdCount,
                  })}
                </li>
                <li>
                  {t("catalogs.csv.errorCount", { count: result.errorCount })}
                </li>
              </ul>
            )}

            {result.errors.length > 0 && (
              <ul
                aria-label={t("catalogs.csv.errorCount", {
                  count: result.errorCount,
                })}
                className="space-y-1 text-sm text-red-700"
              >
                {result.errors.map((rowError) => (
                  <li key={`${rowError.row}-${rowError.message}`}>
                    {t("catalogs.csv.errorDetail", {
                      row: rowError.row,
                      message: rowError.message,
                    })}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {error && <ErrorMessage message={error.message} />}

      <div className="flex gap-2">
        <Button
          type="button"
          onClick={handleUpload}
          isLoading={isPending}
          disabled={!file}
        >
          {t("catalogs.csv.upload")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </section>
  );
}
