import { useTranslation } from "react-i18next";
import { Badge } from "../ui/Badge";
import type { Priority } from "../../types/wishlist";

interface PriorityBadgeProps {
  priority: Priority;
  className?: string;
}

/**
 * PriorityBadge - Badge component for displaying wishlist item priority.
 *
 * Design principle (WCAG 2.1 AA compliance):
 * - Meaning is transmitted with text and icon in addition to color
 * - Priority levels: 1 (highest) to 5 (lowest)
 */
export function PriorityBadge({ priority, className = "" }: PriorityBadgeProps) {
  const { t } = useTranslation();

  const getPriorityConfig = (p: Priority) => {
    switch (p) {
      case 1:
        return {
          tone: "danger" as const,
          label: t("wishlist.priority.critical"),
          icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
              <path fillRule="evenodd" d="M10.868 2.884c-.321-.772-1.415-.772-1.736 0l-1.83 4.401-4.753.381c-.833.067-1.171 1.107-.536 1.651l3.62 3.102-1.106 4.637c-.194.813.691 1.456 1.405 1.02L10 15.591l4.069 2.485c.713.436 1.598-.207 1.404-1.02l-1.106-4.637 3.62-3.102c.635-.544.297-1.584-.536-1.65l-4.752-.382-1.831-4.401Z" clipRule="evenodd" />
            </svg>
          ),
        };
      case 2:
        return {
          tone: "warning" as const,
          label: t("wishlist.priority.high"),
          icon: (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
            </svg>
          ),
        };
      case 3:
        return {
          tone: "neutral" as const,
          label: t("wishlist.priority.medium"),
          icon: null,
        };
      case 4:
        return {
          tone: "neutral" as const,
          label: t("wishlist.priority.low"),
          icon: null,
        };
      case 5:
        return {
          tone: "neutral" as const,
          label: t("wishlist.priority.lowest"),
          icon: null,
        };
    }
  };

  const config = getPriorityConfig(priority);

  return (
    <Badge label={config.label} tone={config.tone} icon={config.icon} className={className} />
  );
}
