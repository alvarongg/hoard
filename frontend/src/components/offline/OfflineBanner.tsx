import { useTranslation } from "react-i18next";
import { useOnlineStatus } from "../../hooks/useOnlineStatus";

/** OfflineBanner - announces offline mode via an aria-live status region. */
export function OfflineBanner() {
  const { t } = useTranslation();
  const online = useOnlineStatus();

  if (online) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-yellow-100 px-4 py-2 text-center text-sm text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200"
    >
      {t("offline.banner")}
    </div>
  );
}
