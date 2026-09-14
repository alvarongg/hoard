/**
 * CompletenessBadge - Badge showing item completeness status.
 *
 * Uses the shared Badge component with appropriate styling and ARIA.
 */

import { useTranslation } from "react-i18next";
import { Badge } from "../ui/Badge";

const CheckIcon = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    fill="currentColor"
    className="h-3 w-3"
    aria-hidden="true"
    focusable="false"
  >
    <path
      fillRule="evenodd"
      d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
      clipRule="evenodd"
    />
  </svg>
);

const XMarkIcon = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    fill="currentColor"
    className="h-3 w-3"
    aria-hidden="true"
    focusable="false"
  >
    <path
      fillRule="evenodd"
      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
      clipRule="evenodd"
    />
  </svg>
);

interface CompletenessBadgeProps {
  /** Whether the item is complete */
  isComplete: boolean;
  /** Number of required components present */
  presentCount: number;
  /** Total number of required components */
  requiredCount: number;
}

export function CompletenessBadge({
  isComplete,
  presentCount,
  requiredCount,
}: CompletenessBadgeProps) {
  const { t } = useTranslation();

  if (isComplete) {
    return (
      <Badge
        label={t("components.complete")}
        tone="success"
        icon={CheckIcon}
      />
    );
  }

  return (
    <Badge
      label={t("components.incomplete", {
        present: presentCount,
        required: requiredCount,
      })}
      tone="warning"
      icon={XMarkIcon}
    />
  );
}
