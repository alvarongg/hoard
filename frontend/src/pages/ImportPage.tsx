import { useTranslation } from "react-i18next";
import { ImportWizard } from "../components/transfer/ImportWizard";

export function ImportPage() {
  const { t } = useTranslation();
  return (
    <main>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t("import.title")}
      </h1>
      <div className="mt-4 max-w-2xl">
        <ImportWizard />
      </div>
    </main>
  );
}
