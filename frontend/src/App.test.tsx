import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { appRoutes } from "./App";
import { ThemeProvider } from "./theme/ThemeProvider";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en", changeLanguage: vi.fn() },
  }),
}));

vi.mock("./hooks/useReducedMotion", () => ({
  useReducedMotion: () => false,
}));

vi.mock("./pages/HomePage", () => ({
  HomePage: () => <div>home-page</div>,
}));
vi.mock("./pages/CollectionsPage", () => ({
  CollectionsPage: () => <div>collections-page</div>,
}));
vi.mock("./pages/CollectionDetailPage", () => ({
  CollectionDetailPage: () => <div>collection-detail-page</div>,
}));
vi.mock("./pages/CatalogsPage", () => ({
  CatalogsPage: () => <div>catalogs-page</div>,
}));
vi.mock("./pages/CatalogDetailPage", () => ({
  CatalogDetailPage: () => <div>catalog-detail-page</div>,
}));
vi.mock("./pages/CatalogManagementPage", () => ({
  CatalogManagementPage: () => <div>catalog-management-page</div>,
}));

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

function renderAt(path: string) {
  window.matchMedia = vi.fn(createMatchMedia(false));
  const router = createMemoryRouter(appRoutes, { initialEntries: [path] });
  return render(
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>,
  );
}

describe("appRoutes", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("renders the catalog management page at /catalogs/manage", async () => {
    renderAt("/catalogs/manage");

    expect(
      await screen.findByText("catalog-management-page"),
    ).toBeInTheDocument();
  });

  it("still renders the catalogs list page at /catalogs", async () => {
    renderAt("/catalogs");

    expect(await screen.findByText("catalogs-page")).toBeInTheDocument();
  });

  it("renders the catalog detail page for a catalog id", async () => {
    renderAt("/catalogs/catalog-1");

    expect(await screen.findByText("catalog-detail-page")).toBeInTheDocument();
  });

  it("renders the navigation link to catalog management inside the layout", async () => {
    renderAt("/catalogs/manage");

    await screen.findByText("catalog-management-page");
    expect(screen.getByText("navigation.catalogManagement")).toHaveAttribute(
      "href",
      "/catalogs/manage",
    );
  });
});
