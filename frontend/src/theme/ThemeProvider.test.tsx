import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ThemeProvider, ThemeContext } from "./ThemeProvider";
import type { ThemeContextValue } from "./types";

// Mock matchMedia
const createMatchMedia = (prefersDark: boolean) => (query: string) => ({
  matches: query === "(prefers-color-scheme: dark)" ? prefersDark : false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
});

const renderWithProvider = (prefersDark = false) => {
  window.matchMedia = vi.fn(createMatchMedia(prefersDark));
  return render(<ThemeProvider>Test Content</ThemeProvider>);
};

describe("ThemeProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("renders children", () => {
    renderWithProvider();
    expect(screen.getByText("Test Content")).toBeInTheDocument();
  });

  it("defaults to auto preference with system light theme", () => {
    renderWithProvider(false);

    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("defaults to auto preference with system dark theme", () => {
    renderWithProvider(true);

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("applies stored light preference on mount", () => {
    localStorage.setItem("hoard.theme", "light");
    renderWithProvider(true);

    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("applies stored dark preference on mount", () => {
    localStorage.setItem("hoard.theme", "dark");
    renderWithProvider(false);

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("updates theme when preference changes", () => {
    let contextValue: ThemeContextValue | null = null;
    render(
      <ThemeProvider>
        <ThemeContext.Consumer>
          {(value) => {
            contextValue = value;
            return null;
          }}
        </ThemeContext.Consumer>
      </ThemeProvider>,
    );

    act(() => {
      contextValue?.setPreference("dark");
    });

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("hoard.theme")).toBe("dark");
  });

  it("clears localStorage when preference is set to auto", () => {
    localStorage.setItem("hoard.theme", "dark");

    let contextValue: ThemeContextValue | null = null;
    render(
      <ThemeProvider>
        <ThemeContext.Consumer>
          {(value) => {
            contextValue = value;
            return null;
          }}
        </ThemeContext.Consumer>
      </ThemeProvider>,
    );

    act(() => {
      contextValue?.setPreference("auto");
    });

    expect(localStorage.getItem("hoard.theme")).toBeNull();
  });

  it("syncs theme across tabs via storage event", () => {
    renderWithProvider(false);

    // Simulate storage event from another tab
    act(() => {
      const storageEvent = new StorageEvent("storage", {
        key: "hoard.theme",
        newValue: "dark",
      });
      window.dispatchEvent(storageEvent);
    });

    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });
});
