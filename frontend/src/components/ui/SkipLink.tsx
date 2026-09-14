import { useTranslation } from "react-i18next";

interface SkipLinkProps {
  targetId: string;
}

/**
 * SkipLink component for keyboard accessibility.
 * Allows keyboard users to skip directly to main content,
 * bypassing repetitive navigation elements.
 *
 * Visually hidden until focused, then appears at top of viewport.
 *
 * @see https://www.w3.org/WAI/WCAG21/Techniques/general/G1
 */
export function SkipLink({ targetId }: SkipLinkProps) {
  const { t } = useTranslation();

  const focusTarget = () => {
    const target = document.getElementById(targetId);
    if (target) {
      // The target (e.g. <main tabIndex={-1}>) is already programmatically
      // focusable. Just move focus to it — do NOT strip its tabindex, which
      // would drop the focus we just set.
      target.focus();
    }
  };

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    focusTarget();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLAnchorElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      focusTarget();
    }
  };

  return (
    <a
      href={`#${targetId}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
    >
      {t("a11y.skipToContent")}
    </a>
  );
}
