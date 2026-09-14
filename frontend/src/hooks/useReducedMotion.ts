/**
 * Hook to detect user's reduced motion preference.
 *
 * Reads `prefers-reduced-motion` media query and reacts to changes.
 * Use this to suppress or reduce animations and transitions for users
 * who have enabled the reduced motion preference in their OS.
 *
 * @returns {boolean} `true` if user prefers reduced motion, `false` otherwise
 *
 * @example
 * function AnimatedComponent() {
 *   const prefersReducedMotion = useReducedMotion();
 *   return (
 *     <div style={{ transition: prefersReducedMotion ? 'none' : 'transform 0.3s' }}>
 *       Content
 *     </div>
 *   );
 * }
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
 * @see https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html
 */

import { useState, useEffect } from "react";

const MEDIA_QUERY = "(prefers-reduced-motion: reduce)";

export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    // SSR guard: default to false on server
    if (typeof window === "undefined") {
      return false;
    }
    return window.matchMedia(MEDIA_QUERY).matches;
  });

  useEffect(() => {
    const mediaQueryList = window.matchMedia(MEDIA_QUERY);

    // Update state when preference changes
    const handleChange = (event: MediaQueryListEvent): void => {
      setPrefersReducedMotion(event.matches);
    };

    // Set initial value (in case it changed since initial state)
    setPrefersReducedMotion(mediaQueryList.matches);

    // Listen for changes using the modern API
    mediaQueryList.addEventListener("change", handleChange);

    return () => {
      mediaQueryList.removeEventListener("change", handleChange);
    };
  }, []);

  return prefersReducedMotion;
}
