import { useTranslation } from "react-i18next";
import { ExportPanel } from "../components/transfer/ExportPanel";

export function ExportPage() {
  const { t } = useTranslation();
  return (
    <main>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("export.title")}
      </h1>
      <div className="mt-4 max-w-md">
        <ExportPanel />
      </div>
    </main>
  );
}
