import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CatalogDetailPage } from "./CatalogDetailPage";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "catalogs.detail": "Catalog Detail",
        "catalogs.items": "Catalog Items",
        "navigation.catalogs": "Catalogs",
        "items.empty": "No items yet",
        "errors.loadFailed": "Failed to load data",
        "errors.notFound": "Resource not found",
        "common.retry": "Retry",
        "ui.loading": "Loading",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started",
      };
      return translations[key] ?? key;
    },
  }),
}));

function renderWithRoute(catalogId: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/catalogs/${catalogId}`]}>
        <Routes>
          <Route
            path="/catalogs/:id"
            element={<CatalogDetailPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CatalogDetailPage", () => {
  it("renders catalog name after loading", async () => {
    renderWithRoute("catalog-1");
    expect(
      await screen.findByRole("heading", { name: "N64 Games Catalog" }),
    ).toBeInTheDocument();
  });

  it("renders catalog description", async () => {
    renderWithRoute("catalog-1");
    expect(await screen.findByText("All N64 games")).toBeInTheDocument();
  });

  it("renders catalog items section heading", async () => {
    renderWithRoute("catalog-1");
    expect(
      await screen.findByText("Catalog Items"),
    ).toBeInTheDocument();
  });

  it("renders catalog item titles", async () => {
    renderWithRoute("catalog-1");
    expect(
      await screen.findByText("The Legend of Zelda: Ocarina of Time"),
    ).toBeInTheDocument();
  });

  it("renders back link to catalogs", async () => {
    renderWithRoute("catalog-1");
    await screen.findByRole("heading", { name: "N64 Games Catalog" });
    expect(
      screen.getByRole("button", { name: "Catalogs" }),
    ).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithRoute("catalog-1");
    await screen.findByRole("heading", { name: "N64 Games Catalog" });
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
