import { createContext, useEffect, useState, useCallback, type ReactNode } from "react";
import type { ThemePreference, ResolvedTheme, ThemeContextValue } from "./types";
import { readPreference, writePreference, clearPreference, STORAGE_KEY } from "./storage";

export const ThemeContext = createContext<ThemeContextValue | null>(null);

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Get the system's preferred color scheme.
 */
function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") {
    return "light";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/**
 * Apply the theme to the document by adding/removing the 'dark' class.
 */
function applyTheme(theme: ResolvedTheme): void {
  const root = document.documentElement;
  if (theme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

/**
 * Theme provider component that handles theme persistence and system preference.
 */
export function ThemeProvider({ children }: ThemeProviderProps): ReactNode {
  const [preference, setPreferenceState] = useState<ThemePreference>(() => readPreference());
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() => {
    const pref = readPreference();
    return pref === "auto" ? getSystemTheme() : pref;
  });

  // Apply theme on mount and when resolvedTheme changes
  useEffect(() => {
    applyTheme(resolvedTheme);
  }, [resolvedTheme]);

  // Listen for system theme changes when preference is 'auto'
  useEffect(() => {
    if (preference !== "auto") {
      return;
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent): void => {
      setResolvedTheme(e.matches ? "dark" : "light");
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [preference]);

  // Listen for storage changes (sync across tabs)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent): void => {
      if (e.key !== STORAGE_KEY) {
        return;
      }

      const newPref = e.newValue as ThemePreference | null;
      if (newPref === "light" || newPref === "dark" || newPref === "auto") {
        setPreferenceState(newPref);
        if (newPref === "auto") {
          setResolvedTheme(getSystemTheme());
        } else {
          setResolvedTheme(newPref);
        }
      } else if (e.newValue === null) {
        // Cleared - default to auto
        setPreferenceState("auto");
        setResolvedTheme(getSystemTheme());
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const setPreference = useCallback((newPreference: ThemePreference): void => {
    setPreferenceState(newPreference);

    if (newPreference === "auto") {
      clearPreference();
      setResolvedTheme(getSystemTheme());
    } else {
      writePreference(newPreference);
      setResolvedTheme(newPreference);
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ preference, resolvedTheme, setPreference }}>
      {children}
    </ThemeContext.Provider>
  );
}
