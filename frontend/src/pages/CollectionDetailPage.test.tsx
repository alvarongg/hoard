import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { CollectionDetailPage } from "./CollectionDetailPage";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "collections.detail": "Collection Detail",
        "collections.items": "Items",
        "navigation.collections": "Collections",
        "items.add": "Add Item",
        "items.empty": "No items yet",
        "items.condition": "Condition",
        "items.excellent": "Excellent",
        "items.price": "Price",
        "items.notes": "Notes",
        "items.catalogItem": "Catalog Item",
        "items.edit": "Edit Item",
        "items.form.selectCatalogItem": "Select catalog item",
        "items.form.selectCondition": "Select condition",
        "items.form.catalogItemRequired": "Catalog item is required",
        "items.form.conditionRequired": "Condition is required",
        "items.mint": "Mint",
        "items.nearMint": "Near Mint",
        "items.good": "Good",
        "items.fair": "Fair",
        "items.poor": "Poor",
        "errors.loadFailed": "Failed to load data",
        "errors.notFound": "Resource not found",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.edit": "Edit",
        "common.loading": "Loading...",
        "common.retry": "Retry",
        "ui.loading": "Loading",
        "ui.close": "Close",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started",
      };
      return translations[key] ?? key;
    },
  }),
}));

function renderWithRoute(collectionId: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/collections/${collectionId}`]}>
        <Routes>
          <Route
            path="/collections/:id"
            element={<CollectionDetailPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CollectionDetailPage", () => {
  beforeEach(() => {
    HTMLDialogElement.prototype.showModal = vi.fn();
    HTMLDialogElement.prototype.close = vi.fn();
  });

  it("renders collection name after loading", async () => {
    renderWithRoute("col-1");
    expect(
      await screen.findByRole("heading", { name: "My N64 Collection" }),
    ).toBeInTheDocument();
  });

  it("renders collection description", async () => {
    renderWithRoute("col-1");
    expect(
      await screen.findByText("Nintendo 64 games"),
    ).toBeInTheDocument();
  });

  it("renders add item button", async () => {
    renderWithRoute("col-1");
    await screen.findByRole("heading", { name: "My N64 Collection" });
    expect(
      screen.getByRole("button", { name: "Add Item" }),
    ).toBeInTheDocument();
  });

  it("renders items section heading", async () => {
    renderWithRoute("col-1");
    expect(await screen.findByText("Items")).toBeInTheDocument();
  });

  it("opens add item modal when button is clicked", async () => {
    const user = userEvent.setup();
    renderWithRoute("col-1");
    await screen.findByRole("heading", { name: "My N64 Collection" });

    await user.click(screen.getByRole("button", { name: "Add Item" }));

    expect(screen.getByLabelText("Catalog Item")).toBeInTheDocument();
  });

  it("renders back link to collections", async () => {
    renderWithRoute("col-1");
    await screen.findByRole("heading", { name: "My N64 Collection" });
    expect(
      screen.getByRole("button", { name: "Collections" }),
    ).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithRoute("col-1");
    await screen.findByRole("heading", { name: "My N64 Collection" });
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
