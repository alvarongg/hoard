import { useTranslation } from "react-i18next";

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <p className="text-lg font-medium text-gray-900">
        {title ?? t("ui.emptyTitle")}
      </p>
      <p className="mt-1 text-sm text-gray-500">
        {description ?? t("ui.emptyDescription")}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
