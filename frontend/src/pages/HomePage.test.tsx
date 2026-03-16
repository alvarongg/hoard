import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "./HomePage";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "home.welcome": "Welcome to H.O.A.R.D.",
        "home.description": "Hobby Organization, Archive & Registry Database",
        "home.quickAccess": "Quick Access",
        "home.totalCollections": "Total Collections",
        "home.totalCatalogs": "Total Catalogs",
        "home.recentCollections": "Your Collections",
        "home.viewAll": "View All",
        "home.getStarted": "Get started by creating your first collection",
        "navigation.collections": "Collections",
        "navigation.catalogs": "Catalogs",
        "errors.loadFailed": "Failed to load data",
        "common.retry": "Retry",
        "ui.loading": "Loading",
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

describe("HomePage", () => {
  it("renders welcome heading", async () => {
    renderWithProviders(<HomePage />);
    expect(
      await screen.findByRole("heading", { name: /welcome to h\.o\.a\.r\.d\./i }),
    ).toBeInTheDocument();
  });

  it("renders description text", async () => {
    renderWithProviders(<HomePage />);
    expect(
      await screen.findByText(/hobby organization/i),
    ).toBeInTheDocument();
  });

  it("renders collection and catalog summary cards", async () => {
    renderWithProviders(<HomePage />);
    expect(await screen.findByText("Total Collections")).toBeInTheDocument();
    expect(screen.getByText("Total Catalogs")).toBeInTheDocument();
  });

  it("renders recent collections section", async () => {
    renderWithProviders(<HomePage />);
    expect(
      await screen.findByText("Your Collections"),
    ).toBeInTheDocument();
  });

  it("renders view all links", async () => {
    renderWithProviders(<HomePage />);
    const viewAllLinks = await screen.findAllByText("View All");
    expect(viewAllLinks.length).toBe(2);
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithProviders(<HomePage />);
    await screen.findByRole("heading", { name: /welcome/i });
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
