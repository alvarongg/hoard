/**
 * SearchModeNotice component for explaining degraded search mode.
 *
 * Requirements: 6.7, 6.10
 */

import { useTranslation } from "react-i18next";
import type { SearchMode } from "../../types/search";

interface SearchModeNoticeProps {
  /** Current search mode */
  mode: SearchMode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Notice explaining the search mode when degraded.
 */
export function SearchModeNotice({ mode, className = "" }: SearchModeNoticeProps) {
  const { t } = useTranslation();

  // Only show notice for degraded mode
  if (mode !== "degraded") {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`rounded-md border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-800 dark:border-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200 ${className}`}
    >
      <div className="flex items-center gap-2">
        <svg
          className="h-4 w-4 shrink-0"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        <p>{t("search.degradedMode")}</p>
      </div>
    </div>
  );
}
