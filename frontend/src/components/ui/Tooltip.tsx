/**
 * Tooltip component for displaying contextual information.
 *
 * Accessible tooltip that appears on both focus (keyboard) and hover (mouse).
 * Uses aria-describedby to associate the tooltip with its trigger element.
 *
 * @example
 * <Tooltip content="Additional information">
 *   <button>Hover or focus me</button>
 * </Tooltip>
 *
 * @see https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/
 */

import { useState, useCallback, useRef, useEffect, ReactElement, cloneElement } from "react";
import { useTranslation } from "react-i18next";

interface TooltipProps {
  /** The content to display inside the tooltip */
  content: string;
  /** The element that triggers the tooltip (must accept ref and aria-describedby) */
  children: ReactElement;
}

// Counter for generating unique tooltip IDs
let tooltipIdCounter = 0;

export function Tooltip({ content, children }: TooltipProps) {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipId] = useState(() => `tooltip-${++tooltipIdCounter}`);

  // Calculate tooltip position based on trigger element
  const updatePosition = useCallback(() => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPosition({
        top: rect.bottom + 8, // 8px gap
        left: rect.left,
      });
    }
  }, []);

  const showTooltip = useCallback(() => {
    setIsVisible(true);
    updatePosition();
  }, [updatePosition]);

  const hideTooltip = useCallback(() => {
    setIsVisible(false);
  }, []);

  // Update position on scroll/resize
  useEffect(() => {
    if (!isVisible) {
      return;
    }

    const handleReposition = () => updatePosition();
    window.addEventListener("scroll", handleReposition, true);
    window.addEventListener("resize", handleReposition);

    return () => {
      window.removeEventListener("scroll", handleReposition, true);
      window.removeEventListener("resize", handleReposition);
    };
  }, [isVisible, updatePosition]);

  // Handle Escape key to close tooltip
  useEffect(() => {
    if (isVisible) {
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          hideTooltip();
          triggerRef.current?.focus();
        }
      };

      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isVisible, hideTooltip]);

  // Clone the child element to add tooltip props
  const triggerWithProps = cloneElement(children, {
    ref: triggerRef,
    "aria-describedby": isVisible ? tooltipId : undefined,
    onFocus: (e: React.FocusEvent) => {
      showTooltip();
      children.props.onFocus?.(e);
    },
    onBlur: (e: React.FocusEvent) => {
      hideTooltip();
      children.props.onBlur?.(e);
    },
    onMouseEnter: (e: React.MouseEvent) => {
      showTooltip();
      children.props.onMouseEnter?.(e);
    },
    onMouseLeave: (e: React.MouseEvent) => {
      hideTooltip();
      children.props.onMouseLeave?.(e);
    },
  });

  return (
    <>
      {triggerWithProps}
      {isVisible && (
        <div
          ref={tooltipRef}
          id={tooltipId}
          role="tooltip"
          className="fixed z-50 max-w-xs rounded-md bg-gray-900 px-3 py-2 text-sm text-white shadow-lg"
          style={{ top: position.top, left: position.left }}
          aria-hidden="false"
        >
          {content}
          <span className="sr-only">
            {t("a11y.pressEscapeToClose", { defaultValue: "Press Escape to close" })}
          </span>
        </div>
      )}
    </>
  );
}
