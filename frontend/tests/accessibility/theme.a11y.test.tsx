/**
 * Accessibility tests for theme contrast in both light and dark modes.
 * Runs axe-core on key pages to verify WCAG 2.1 AA contrast requirements.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { ThemeProvider } from "../../src/theme/ThemeProvider";

expect.extend(toHaveNoViolations);

// Mock i18n
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

vi.mock("../../src/hooks/useReducedMotion", () => ({
  useReducedMotion: () => false,
}));

// Mock pages
vi.mock("../../src/pages/HomePage", () => ({
  HomePage: () => (
    <div>
      <h1>Home</h1>
      <p>Welcome to H.O.A.R.D.</p>
    </div>
  ),
}));
vi.mock("../../src/pages/CollectionsPage", () => ({
  CollectionsPage: () => (
    <div>
      <h1>Collections</h1>
      <p>Your collections list</p>
    </div>
  ),
}));
vi.mock("../../src/pages/CatalogsPage", () => ({
  CatalogsPage: () => (
    <div>
      <h1>Catalogs</h1>
      <p>Your catalogs list</p>
    </div>
  ),
}));
vi.mock("../../src/pages/CatalogDetailPage", () => ({
  CatalogDetailPage: () => (
    <div>
      <h1>Catalog Detail</h1>
      <p>Catalog details page</p>
    </div>
  ),
}));
vi.mock("../../src/pages/CatalogManagementPage", () => ({
  CatalogManagementPage: () => (
    <div>
      <h1>Catalog Management</h1>
      <p>Manage your catalogs</p>
    </div>
  ),
}));
vi.mock("../../src/pages/CollectionDetailPage", () => ({
  CollectionDetailPage: () => (
    <div>
      <h1>Collection Detail</h1>
      <p>Collection details page</p>
    </div>
  ),
}));

// Mock API hooks
vi.mock("../../src/hooks/useCollections", () => ({
  useCollections: () => ({ data: [], isLoading: false, error: null }),
}));

vi.mock("../../src/hooks/useCatalogs", () => ({
  useCatalogs: () => ({ data: [], isLoading: false, error: null }),
}));

import { appRoutes } from "../../src/App";

// Mock matchMedia for ThemeProvider
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

function renderWithTheme(path: string, isDark: boolean) {
  window.matchMedia = vi.fn(createMatchMedia(isDark));

  // Set the dark class before rendering
  if (isDark) {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }

  const router = createMemoryRouter(appRoutes, { initialEntries: [path] });
  return render(
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>,
  );
}

describe("Theme Accessibility", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  describe("Light Theme", () => {
    beforeAll(() => {
      document.documentElement.classList.remove("dark");
    });

    it("has no contrast violations on home page", async () => {
      const { container } = renderWithTheme("/", false);
      await screen.findByText("Home");

      const results = await axe(container, {
        rules: {
          "color-contrast": { enabled: true },
        },
      });
      expect(results).toHaveNoViolations();
    });

    it("has no contrast violations on collections page", async () => {
      const { container } = renderWithTheme("/collections", false);
      await screen.findByText("Collections");

      const results = await axe(container, {
        rules: {
          "color-contrast": { enabled: true },
        },
      });
      expect(results).toHaveNoViolations();
    });

    it("has no contrast violations on catalogs page", async () => {
      const { container } = renderWithTheme("/catalogs", false);
      await screen.findByText("Catalogs");

      const results = await axe(container, {
        rules: {
          "color-contrast": { enabled: true },
        },
      });
      expect(results).toHaveNoViolations();
    });
  });

  describe("Dark Theme", () => {
    beforeAll(() => {
      document.documentElement.classList.add("dark");
    });

    it("has no contrast violations on home page", async () => {
      const { container } = renderWithTheme("/", true);
      await screen.findByText("Home");

      const results = await axe(container, {
        rules: {
          "color-contrast": { enabled: true },
        },
      });
      expect(results).toHaveNoViolations();
    });

    it("has no contrast violations on collections page", async () => {
      const { container } = renderWithTheme("/collections", true);
      await screen.findByText("Collections");

      const results = await axe(container, {
        rules: {
          "color-contrast": { enabled: true },
        },
      });
      expect(results).toHaveNoViolations();
    });

    it("has no contrast violations on catalogs page", async () => {
      const { container } = renderWithTheme("/catalogs", true);
      await screen.findByText("Catalogs");

      const results = await axe(container, {
        rules: {
          "color-contrast": { enabled: true },
        },
      });
      expect(results).toHaveNoViolations();
    });
  });
});
