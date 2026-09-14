/**
 * Per-page accessibility audit: runs axe-core (full WCAG 2.1 AA ruleset) over
 * every route in both light and dark themes, requiring zero violations.
 *
 * Pages are mocked to lightweight landmark content so the audit exercises the
 * routing + layout shell (skip link, nav, main landmark, headings, theme
 * tokens) deterministically in jsdom. Component-level axe coverage lives in
 * each component's own *.test.tsx.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { ThemeProvider } from "../../src/theme/ThemeProvider";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

vi.mock("../../src/hooks/useReducedMotion", () => ({
  useReducedMotion: () => false,
}));

// Lightweight page stubs, each a single <h1> landmark. Factories are hoisted,
// so the JSX must be inlined (no shared helper reference).
vi.mock("../../src/pages/HomePage", () => ({ HomePage: () => <h1>Home</h1> }));
vi.mock("../../src/pages/CollectionsPage", () => ({
  CollectionsPage: () => <h1>Collections</h1>,
}));
vi.mock("../../src/pages/CollectionDetailPage", () => ({
  CollectionDetailPage: () => <h1>Collection Detail</h1>,
}));
vi.mock("../../src/pages/CatalogsPage", () => ({
  CatalogsPage: () => <h1>Catalogs</h1>,
}));
vi.mock("../../src/pages/CatalogManagementPage", () => ({
  CatalogManagementPage: () => <h1>Catalog Management</h1>,
}));
vi.mock("../../src/pages/CatalogDetailPage", () => ({
  CatalogDetailPage: () => <h1>Catalog Detail</h1>,
}));
vi.mock("../../src/pages/SuppliersPage", () => ({
  SuppliersPage: () => <h1>Suppliers</h1>,
}));
vi.mock("../../src/pages/WishlistPage", () => ({
  WishlistPage: () => <h1>Wishlist</h1>,
}));
vi.mock("../../src/pages/WishlistDetailPage", () => ({
  WishlistDetailPage: () => <h1>Wishlist Detail</h1>,
}));
vi.mock("../../src/pages/SearchPage", () => ({
  SearchPage: () => <h1>Search</h1>,
}));
vi.mock("../../src/pages/StatsPage", () => ({ StatsPage: () => <h1>Stats</h1> }));
vi.mock("../../src/pages/AccessoriesPage", () => ({
  AccessoriesPage: () => <h1>Accessories</h1>,
}));
vi.mock("../../src/pages/ExportPage", () => ({
  ExportPage: () => <h1>Export</h1>,
}));
vi.mock("../../src/pages/ImportPage", () => ({
  ImportPage: () => <h1>Import</h1>,
}));
vi.mock("../../src/pages/BackupsPage", () => ({
  BackupsPage: () => <h1>Backups</h1>,
}));

import { appRoutes } from "../../src/App";

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

function renderRoute(path: string, isDark: boolean) {
  window.matchMedia = vi.fn(createMatchMedia(isDark));
  document.documentElement.classList.toggle("dark", isDark);
  const router = createMemoryRouter(appRoutes, { initialEntries: [path] });
  return render(
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>,
  );
}

const ROUTES: Array<[string, string]> = [
  ["/", "Home"],
  ["/collections", "Collections"],
  ["/collections/c1", "Collection Detail"],
  ["/catalogs", "Catalogs"],
  ["/catalogs/manage", "Catalog Management"],
  ["/catalogs/c1", "Catalog Detail"],
  ["/suppliers", "Suppliers"],
  ["/wishlist", "Wishlist"],
  ["/wishlist/w1", "Wishlist Detail"],
  ["/search", "Search"],
  ["/stats", "Stats"],
  ["/accessories", "Accessories"],
  ["/export", "Export"],
  ["/import", "Import"],
  ["/settings/backups", "Backups"],
];

describe("Per-page accessibility audit", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  for (const isDark of [false, true]) {
    const themeName = isDark ? "dark" : "light";
    describe(`${themeName} theme`, () => {
      for (const [path, heading] of ROUTES) {
        it(`has no violations at ${path}`, async () => {
          const { container } = renderRoute(path, isDark);
          await screen.findByText(heading);
          const results = await axe(container);
          expect(results).toHaveNoViolations();
        });
      }
    });
  }
});
