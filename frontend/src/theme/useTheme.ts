import { useContext } from "react";
import { ThemeContext } from "./ThemeProvider";
import type { ThemeContextValue } from "./types";

/**
 * Hook to access the theme context.
 * @returns The theme context value with preference, resolvedTheme, and setPreference.
 * @throws Error if used outside of ThemeProvider.
 */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
