import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { CatalogsPage } from "./CatalogsPage";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "catalogs.title": "Catalogs",
        "catalogs.empty": "No catalogs yet",
        "catalogs.search": "Search items...",
        "common.search": "Search",
        "common.noResults": "No results found",
        "errors.loadFailed": "Failed to load data",
        "common.retry": "Retry",
        "ui.loading": "Loading",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started",
        "collections.itemCount": `${opts?.count ?? 0} items`,
      };
      return translations[key] ?? key;
    },
  }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CatalogsPage", () => {
  it("renders page heading", () => {
    renderWithProviders(<CatalogsPage />);
    expect(
      screen.getByRole("heading", { name: "Catalogs" }),
    ).toBeInTheDocument();
  });

  it("renders search input", async () => {
    renderWithProviders(<CatalogsPage />);
    expect(await screen.findByLabelText("Search")).toBeInTheDocument();
  });

  it("renders catalog list after loading", async () => {
    renderWithProviders(<CatalogsPage />);
    expect(
      await screen.findByText("N64 Games Catalog"),
    ).toBeInTheDocument();
  });

  it("filters catalogs by search term", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CatalogsPage />);
    await screen.findByText("N64 Games Catalog");

    await user.type(screen.getByLabelText("Search"), "nonexistent");

    expect(screen.queryByText("N64 Games Catalog")).not.toBeInTheDocument();
    expect(screen.getByText("No results found")).toBeInTheDocument();
  });

  it("shows catalog item count", async () => {
    renderWithProviders(<CatalogsPage />);
    expect(await screen.findByText("296 items")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithProviders(<CatalogsPage />);
    await screen.findByText("N64 Games Catalog");
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
