import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { SearchPage } from "./SearchPage";
import { server } from "../test/mocks/server";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "search.title": "Search",
        "search.results": "Results",
        "search.placeholder": "Search the catalog",
        "search.searchHint": "Type to search",
        "search.clearSearch": "Clear search",
        "search.noResults": "No results found",
        "search.noResultsHint": "Try adjusting your filters",
        "search.enterQuery": "Enter a query to search",
        "search.searching": "Searching...",
        "search.pagination": "Search results pagination",
        "search.resultsLabel": "Search results",
        "search.degradedMode": "Search is running in degraded mode",
        "search.filters.title": "Filters",
        "search.filters.yearMin": "Year (from)",
        "search.filters.yearMax": "Year (to)",
        "search.filters.manufacturer": "Manufacturer",
        "search.filters.publisher": "Publisher",
        "search.filters.developer": "Developer",
        "search.filters.brand": "Brand",
        "search.resultCount": `${opts?.count ?? 0} results`,
        "search.pageStatus": `Page ${opts?.current ?? 1} of ${opts?.total ?? 1}`,
        "errors.searchFailed": "Search failed",
        "common.previous": "Previous",
        "common.next": "Next",
        "common.all": "All",
        "common.loading": "Loading...",
        "common.clearFilters": "Clear filters",
        "common.retry": "Retry",
      };
      return translations[key] ?? key;
    },
  }),
}));

/** Base URL used by the MSW handlers (matches services/api base). */
const API_URL = "http://localhost:8000/api";

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

describe("SearchPage", () => {
  beforeEach(() => {
    // Default search handler: returns two results in degraded mode.
    server.use(
      http.get(`${API_URL}/search/catalog-items`, () => {
        return HttpResponse.json({
          items: [
            {
              id: "cat-item-1",
              title: "The Legend of Zelda: Ocarina of Time",
              subtitle: "Nintendo 64",
              catalog_id: "catalog-1",
            },
            {
              id: "cat-item-2",
              title: "Super Mario 64",
              subtitle: null,
              catalog_id: "catalog-1",
            },
          ],
          total: 2,
          search_mode: "degraded",
        });
      }),
    );
  });

  it("renders the page heading", () => {
    renderWithProviders(<SearchPage />);
    expect(
      screen.getByRole("heading", { name: "Search", level: 1 }),
    ).toBeInTheDocument();
  });

  it("renders the search input", () => {
    renderWithProviders(<SearchPage />);
    expect(
      screen.getByRole("searchbox", { name: "Search the catalog" }),
    ).toBeInTheDocument();
  });

  it("renders an empty-state prompt before any query is entered", () => {
    renderWithProviders(<SearchPage />);
    expect(
      screen.getByText("Enter a query to search"),
    ).toBeInTheDocument();
  });

  it("exposes the results region with an accessible name", () => {
    renderWithProviders(<SearchPage />);
    expect(
      screen.getByRole("region", { name: "Results" }),
    ).toBeInTheDocument();
  });

  it("shows the degraded search-mode notice", () => {
    renderWithProviders(<SearchPage />);
    expect(
      screen.getByText("Search is running in degraded mode"),
    ).toBeInTheDocument();
  });

  it("shows results after typing a query", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);

    await user.type(
      screen.getByRole("searchbox", { name: "Search the catalog" }),
      "zelda",
    );

    expect(
      await screen.findByText("The Legend of Zelda: Ocarina of Time"),
    ).toBeInTheDocument();
    expect(screen.getByText("Super Mario 64")).toBeInTheDocument();
  });

  it("renders results as an accessible listbox of options", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);

    await user.type(
      screen.getByRole("searchbox", { name: "Search the catalog" }),
      "mario",
    );

    await screen.findByText("Super Mario 64");
    expect(
      screen.getByRole("listbox", { name: "Search results" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(2);
  });

  it("shows an error state with a retry action when the search fails", async () => {
    server.use(
      http.get(`${API_URL}/search/catalog-items`, () => {
        return HttpResponse.json({ detail: "boom" }, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);

    await user.type(
      screen.getByRole("searchbox", { name: "Search the catalog" }),
      "zelda",
    );

    expect(await screen.findByText("Search failed")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /retry/i }),
    ).toBeInTheDocument();
  });

  it("keeps interactive controls reachable by keyboard", async () => {
    const user = userEvent.setup();
    renderWithProviders(<SearchPage />);

    await user.tab();
    expect(
      screen.getByRole("searchbox", { name: "Search the catalog" }),
    ).toHaveFocus();
  });

  it("has no accessibility violations in the empty state", async () => {
    const { container } = renderWithProviders(<SearchPage />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with results", async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<SearchPage />);

    await user.type(
      screen.getByRole("searchbox", { name: "Search the catalog" }),
      "zelda",
    );
    await screen.findByText("The Legend of Zelda: Ocarina of Time");

    await waitFor(async () => {
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
