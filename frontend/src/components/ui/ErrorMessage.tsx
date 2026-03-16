import { useTranslation } from "react-i18next";

interface ErrorMessageProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  const { t } = useTranslation();

  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4">
      <p className="text-sm text-red-700">
        {message ?? t("errors.generic")}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 text-sm font-medium text-red-600 underline hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          aria-label={t("common.retry")}
        >
          {t("common.retry")}
        </button>
      )}
    </div>
  );
}
