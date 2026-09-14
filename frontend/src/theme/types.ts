/**
 * Theme types for the H.O.A.R.D. application.
 */

export type ThemePreference = "light" | "dark" | "auto";
export type ResolvedTheme = "light" | "dark";

export interface ThemeContextValue {
  /** The user's explicit preference (light, dark, or auto) */
  preference: ThemePreference;
  /** The resolved theme based on preference and system setting */
  resolvedTheme: ResolvedTheme;
  /** Update the theme preference */
  setPreference: (preference: ThemePreference) => void;
}
