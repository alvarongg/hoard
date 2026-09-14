import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { WishlistPage } from "./WishlistPage";

expect.extend(toHaveNoViolations);

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "wishlist.title": "Wishlist",
        "wishlist.create": "Add to Wishlist",
        "wishlist.edit": "Edit Wishlist Item",
        "wishlist.delete": "Delete",
        "wishlist.empty": "Your wishlist is empty",
        "wishlist.deleteConfirm": "Delete this item?",
        "wishlist.acquired": "Acquired",
        "wishlist.inactive": "Inactive",
        "wishlist.budget": "Budget",
        "wishlist.condition": "Condition",
        "wishlist.mustBeComplete": "Must be complete",
        "wishlist.viewDetails": "View details",
        "wishlist.itemTitle": `Item ${opts?.id ?? ""}`,
        "wishlist.filters.priority": "Priority",
        "wishlist.filters.urgency": "Urgency",
        "wishlist.filters.status": "Status",
        "wishlist.filters.activeOnly": "Active only",
        "wishlist.filters.inactiveOnly": "Inactive only",
        "wishlist.filters.includeAcquired": "Include acquired",
        "wishlist.priority.critical": "Critical",
        "wishlist.priority.high": "High",
        "wishlist.priority.medium": "Medium",
        "wishlist.priority.low": "Low",
        "wishlist.priority.lowest": "Lowest",
        "wishlist.urgency.critical": "Critical",
        "wishlist.urgency.high": "High",
        "wishlist.urgency.medium": "Medium",
        "wishlist.urgency.low": "Low",
        "wishlist.form.priority": "Priority",
        "wishlist.form.urgency": "Urgency",
        "wishlist.form.maxPrice": "Max Price",
        "wishlist.form.currency": "Currency",
        "wishlist.form.desiredCondition": "Desired Condition",
        "wishlist.form.mustBeComplete": "Must be complete",
        "wishlist.form.completenessDescription": "Completeness description",
        "wishlist.form.specificVariantRequired": "Specific variant required",
        "wishlist.form.variantDescription": "Variant description",
        "wishlist.form.notes": "Notes",
        "wishlist.form.searchNotes": "Search notes",
        "wishlist.form.status": "Status",
        "wishlist.form.active": "Active",
        "wishlist.form.inactive": "Inactive",
        "common.all": "All",
        "common.view": "View",
        "common.edit": "Edit",
        "common.delete": "Delete",
        "common.save": "Save",
        "common.create": "Create",
        "common.saving": "Saving...",
        "common.cancel": "Cancel",
        "common.clearFilters": "Clear filters",
        "ui.close": "Close",
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

describe("WishlistPage", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    HTMLDialogElement.prototype.showModal = vi.fn();
    HTMLDialogElement.prototype.close = vi.fn();
  });

  it("renders page heading", () => {
    renderWithProviders(<WishlistPage />);
    expect(
      screen.getByRole("heading", { name: "Wishlist", level: 1 }),
    ).toBeInTheDocument();
  });

  it("renders the create button", () => {
    renderWithProviders(<WishlistPage />);
    expect(
      screen.getByRole("button", { name: "Add to Wishlist" }),
    ).toBeInTheDocument();
  });

  it("renders the filter controls", () => {
    renderWithProviders(<WishlistPage />);
    expect(
      screen.getByRole("combobox", { name: "Priority" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Urgency" }),
    ).toBeInTheDocument();
  });

  it("renders the wishlist items after loading", async () => {
    renderWithProviders(<WishlistPage />);
    expect(await screen.findByText("Item wish-1")).toBeInTheDocument();
  });

  it("renders items inside a semantic list", async () => {
    renderWithProviders(<WishlistPage />);
    await screen.findByText("Item wish-1");
    const list = screen.getByRole("list");
    expect(list).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
  });

  it("opens the create modal when the create button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<WishlistPage />);

    await user.click(screen.getByRole("button", { name: "Add to Wishlist" }));

    expect(
      screen.getByRole("combobox", { name: "Priority" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Max Price")).toBeInTheDocument();
  });

  it("navigates to the detail page when view is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<WishlistPage />);
    await screen.findByText("Item wish-1");

    await user.click(screen.getByRole("button", { name: "View details" }));

    expect(mockNavigate).toHaveBeenCalledWith("/wishlist/wish-1");
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithProviders(<WishlistPage />);
    await screen.findByText("Item wish-1");
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
