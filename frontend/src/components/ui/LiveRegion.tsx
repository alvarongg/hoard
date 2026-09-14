/**
 * LiveRegion component for announcing dynamic content changes to screen readers.
 *
 * This component renders a visually hidden container that uses ARIA live regions
 * to announce messages to assistive technologies. Use it to announce status
 * changes, success messages, errors, and other dynamic updates.
 *
 * @example
 * // For polite announcements (non-critical, announced after current speech)
 * <LiveRegion message="Item added to collection" />
 *
 * @example
 * // For assertive announcements (critical, interrupts current speech)
 * <LiveRegion message="Error saving changes" politeness="assertive" />
 *
 * @see https://www.w3.org/WAI/ARIA/apg/practices/live-region/
 */

interface LiveRegionProps {
  /** The message to announce to screen readers */
  message: string;
  /**
   * The politeness level of the announcement.
   * - "polite" (default): Announced after current speech finishes
   * - "assertive": Interrupts current speech immediately
   */
  politeness?: "polite" | "assertive";
}

export function LiveRegion({ message, politeness = "polite" }: LiveRegionProps) {
  return (
    <div
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
}
