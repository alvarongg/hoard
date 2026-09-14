import { useTranslation } from "react-i18next";
import { Badge } from "../ui/Badge";
import type { Urgency } from "../../types/wishlist";

interface UrgencyBadgeProps {
  urgency: Urgency;
  className?: string;
}

/**
 * UrgencyBadge - Badge component for displaying wishlist item urgency.
 *
 * Design principle (WCAG 2.1 AA compliance):
 * - Meaning is transmitted with text and icon in addition to color
 * - Urgency levels: low, medium, high, critical
 */
export function UrgencyBadge({ urgency, className = "" }: UrgencyBadgeProps) {
  const { t } = useTranslation();

  const getUrgencyConfig = (u: Urgency) => {
    switch (u) {
      case "critical":
        return {
          tone: "danger" as const,
          label: t("wishlist.urgency.critical"),
          icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
              <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          ),
        };
      case "high":
        return {
          tone: "warning" as const,
          label: t("wishlist.urgency.high"),
          icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5a.75.75 0 001.5 0V5zm0 8a.75.75 0 00-1.5 0v1a.75.75 0 001.5 0v-1z" clipRule="evenodd" />
            </svg>
          ),
        };
      case "medium":
        return {
          tone: "neutral" as const,
          label: t("wishlist.urgency.medium"),
          icon: null,
        };
      case "low":
        return {
          tone: "neutral" as const,
          label: t("wishlist.urgency.low"),
          icon: null,
        };
    }
  };

  const config = getUrgencyConfig(urgency);

  return (
    <Badge label={config.label} tone={config.tone} icon={config.icon} className={className} />
  );
}
