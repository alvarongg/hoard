/**
 * Theme preference storage utilities.
 * Handles localStorage access safely with error handling for environments
 * where localStorage may not be available (SSR, private browsing, etc.).
 */

import type { ThemePreference } from "./types";

export const STORAGE_KEY = "hoard.theme";

/**
 * Read the stored theme preference from localStorage.
 * Returns "auto" if no valid preference is stored or if localStorage is unavailable.
 */
export function readPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "auto") {
      return stored;
    }
  } catch {
    // localStorage not available (SSR, private browsing, etc.)
  }
  return "auto";
}

/**
 * Write the theme preference to localStorage.
 * Silently fails if localStorage is unavailable.
 */
export function writePreference(preference: ThemePreference): void {
  try {
    localStorage.setItem(STORAGE_KEY, preference);
  } catch {
    // localStorage not available
  }
}

/**
 * Clear the theme preference from localStorage.
 * Silently fails if localStorage is unavailable.
 */
export function clearPreference(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // localStorage not available
  }
}
