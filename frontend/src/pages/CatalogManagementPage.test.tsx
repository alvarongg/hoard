import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { mockCatalog, mockCatalogItem } from "../test/mocks/handlers";
import { CatalogManagementPage } from "./CatalogManagementPage";

expect.extend(toHaveNoViolations);

const API_URL = "http://localhost:8000/api";
const ZELDA_TITLE = "The Legend of Zelda: Ocarina of Time";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "catalogs.management.title": "Catalog Management",
        "catalogs.management.selectCatalog": "Select catalog",
        "catalogs.management.addItem": "Add item",
        "catalogs.management.importCsv": "Import CSV",
        "catalogs.management.noCatalogs": "No catalogs available",
        "catalogs.management.noItems": "No items in this catalog",
        "catalogs.management.pagination": "Catalog items pagination",
        "catalogs.management.previousPage": "Previous page",
        "catalogs.management.nextPage": "Next page",
        "catalogs.items": "Catalog Items",
        "catalogs.csv.upload": "Upload CSV",
        "catalogs.csv.selectFile": "Select CSV file",
        "catalogs.csv.importing": "Importing",
        "catalogs.csv.importComplete": "Import complete",
        "errors.loadFailed": "Failed to load data",
        "common.retry": "Retry",
        "ui.loading": "Loading",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started",
        "items.inline.createNew": "Create new item",
        "items.inline.title": "Title",
        "items.inline.showOptional": "Show optional fields",
        "items.inline.optionalFields": "Optional fields",
        "common.save": "Save",
        "common.cancel": "Cancel",
      };
      if (key === "catalogs.management.itemCount") {
        return `${opts?.count ?? 0} items`;
      }
      if (key === "catalogs.management.pageStatus") {
        return `Page ${opts?.current ?? 1} of ${opts?.total ?? 1}`;
      }
      return translations[key] ?? key;
    },
  }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CatalogManagementPage", () => {
  it("renders the page heading", () => {
    renderWithProviders(<CatalogManagementPage />);
    expect(
      screen.getByRole("heading", { name: "Catalog Management", level: 1 }),
    ).toBeInTheDocument();
  });

  it("renders a catalog selector listing available catalogs", async () => {
    renderWithProviders(<CatalogManagementPage />);

    const selector = await screen.findByLabelText("Select catalog");
    expect(selector).toBeInTheDocument();
    expect(
      within(selector).getByRole("option", { name: mockCatalog.name }),
    ).toBeInTheDocument();
  });

  it("renders the items of the selected catalog", async () => {
    renderWithProviders(<CatalogManagementPage />);

    const section = await screen.findByRole("region", {
      name: "Catalog Items",
    });
    expect(await within(section).findByText(ZELDA_TITLE)).toBeInTheDocument();
    expect(within(section).getByText("1 items")).toBeInTheDocument();
  });

  it("renders an empty state when there are no catalogs", async () => {
    server.use(
      http.get(`${API_URL}/catalogs`, () => HttpResponse.json([])),
    );
    renderWithProviders(<CatalogManagementPage />);

    expect(
      await screen.findByText("No catalogs available"),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Select catalog")).not.toBeInTheDocument();
  });

  it("renders an empty state when the selected catalog has no items", async () => {
    server.use(
      http.get(`${API_URL}/catalogs/:id/items`, () => HttpResponse.json([])),
    );
    renderWithProviders(<CatalogManagementPage />);

    await waitFor(() => {
      expect(screen.getByText("No items in this catalog")).toBeInTheDocument();
    });
    expect(screen.getByText("0 items")).toBeInTheDocument();
  });

  it("shows the inline catalog item form when clicking add item", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CatalogManagementPage />);
    await screen.findByText(ZELDA_TITLE);

    await user.click(screen.getByRole("button", { name: "Add item" }));

    expect(
      await screen.findByRole("heading", { name: "Create new item" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
  });

  it("shows the CSV upload form when clicking import CSV", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CatalogManagementPage />);
    await screen.findByText(ZELDA_TITLE);

    await user.click(screen.getByRole("button", { name: "Import CSV" }));

    expect(
      await screen.findByRole("heading", { name: "Upload CSV" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Select CSV file")).toBeInTheDocument();
  });

  it("adds an inline created item to the list without a reload", async () => {
    const newItem = {
      ...mockCatalogItem,
      id: "cat-item-2",
      title: "Super Mario 64",
    };
    let created = false;

    server.use(
      http.get(`${API_URL}/catalogs/:id/items`, () =>
        HttpResponse.json(created ? [mockCatalogItem, newItem] : [mockCatalogItem]),
      ),
      http.post(`${API_URL}/catalogs/:id/items`, async () => {
        created = true;
        return HttpResponse.json(newItem, { status: 201 });
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<CatalogManagementPage />);
    await screen.findByText(ZELDA_TITLE);

    await user.click(screen.getByRole("button", { name: "Add item" }));
    await user.type(await screen.findByLabelText(/Title/), "Super Mario 64");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Super Mario 64")).toBeInTheDocument();
    expect(screen.getByText(ZELDA_TITLE)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Create new item" }),
    ).not.toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithProviders(<CatalogManagementPage />);
    await screen.findByText(ZELDA_TITLE);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
