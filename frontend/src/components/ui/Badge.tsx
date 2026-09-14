import type { ReactNode } from "react";

type BadgeTone = "neutral" | "success" | "warning" | "danger";

interface BadgeProps {
  label: string;
  tone: BadgeTone;
  icon?: ReactNode;
  className?: string;
}

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "bg-gray-100 text-gray-800 border-gray-200",
  success: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
  danger: "bg-red-100 text-red-800 border-red-200",
};

/**
 * Badge component for displaying status or category labels.
 *
 * Design principle (WCAG 2.1 AA compliance):
 * - Meaning is transmitted with text (label) and icon in addition to color
 * - Never relies solely on color to convey information
 *
 * @param label - The text content of the badge (required for meaning)
 * @param tone - Visual styling variant (neutral, success, warning, danger)
 * @param icon - Optional icon that reinforces the meaning
 * @param className - Optional additional CSS classes
 */
export function Badge({ label, tone, icon, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]} ${className}`}
      role="status"
    >
      {icon && <span aria-hidden="true">{icon}</span>}
      <span>{label}</span>
    </span>
  );
}
