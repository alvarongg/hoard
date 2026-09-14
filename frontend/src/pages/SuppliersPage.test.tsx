import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { SuppliersPage } from "./SuppliersPage";
import type { Supplier } from "../types/supplier";

expect.extend(toHaveNoViolations);

// ---- i18n mock ---------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "suppliers.title": "Suppliers",
        "suppliers.create": "Create Supplier",
        "suppliers.edit": "Edit Supplier",
        "suppliers.delete": "Delete Supplier",
        "suppliers.empty": "No suppliers yet",
        "suppliers.deleteConfirm": `Delete ${opts?.name ?? ""}?`,
        "suppliers.favorite": "Mark as favorite",
        "suppliers.unfavorite": "Remove from favorites",
        "suppliers.typeOptions.online": "Online Store",
        "suppliers.name": "Name",
        "suppliers.type": "Type",
        "suppliers.country": "Country",
        "suppliers.city": "City",
        "suppliers.rating": "Rating",
        "suppliers.notes": "Notes",
        "suppliers.active": "Active",
        "errors.loadFailed": "Failed to load data",
        "errors.deleteFailed": "Delete failed",
        "common.edit": "Edit",
        "common.delete": "Delete",
        "common.cancel": "Cancel",
        "common.save": "Save",
        "common.loading": "Loading...",
        "common.retry": "Retry",
        "ui.loading": "Loading",
        "ui.close": "Close",
      };
      return translations[key] ?? key;
    },
  }),
}));

// ---- useSuppliers hook mock -------------------------------------------
const mockCreate = { mutate: vi.fn(), isPending: false };
const mockUpdate = { mutate: vi.fn(), isPending: false };
const mockRemove = {
  mutate: vi.fn(),
  isPending: false,
  isError: false,
  error: null as Error | null,
};
const mockToggleFavorite = { mutate: vi.fn() };

let mockHookState: {
  data: Supplier[] | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: ReturnType<typeof vi.fn>;
};

vi.mock("../hooks/useSuppliers", () => ({
  useSuppliers: () => ({
    ...mockHookState,
    create: mockCreate,
    update: mockUpdate,
    remove: mockRemove,
    toggleFavorite: mockToggleFavorite,
  }),
}));

const baseSupplier: Supplier = {
  id: "supplier-1",
  name: "Acme Games",
  type: "online",
  country: "US",
  stateProvince: null,
  city: "New York",
  address: null,
  postalCode: null,
  website: "https://acme-games.example.com",
  email: null,
  phone: null,
  marketplaceUrl: null,
  socialMedia: null,
  rating: 4.5,
  notes: null,
  isFavorite: false,
  isActive: true,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

function setHookState(overrides: Partial<typeof mockHookState> = {}) {
  mockHookState = {
    data: [baseSupplier],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

describe("SuppliersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRemove.isError = false;
    mockRemove.error = null;
    // jsdom does not implement the <dialog> API used by Modal.
    HTMLDialogElement.prototype.showModal = vi.fn();
    HTMLDialogElement.prototype.close = vi.fn();
    setHookState();
  });

  it("renders the page heading", () => {
    render(<SuppliersPage />);
    expect(
      screen.getByRole("heading", { name: "Suppliers", level: 1 }),
    ).toBeInTheDocument();
  });

  it("renders the create button", () => {
    render(<SuppliersPage />);
    expect(
      screen.getByRole("button", { name: "Create Supplier" }),
    ).toBeInTheDocument();
  });

  it("renders the list of suppliers", () => {
    render(<SuppliersPage />);
    expect(
      screen.getByRole("heading", { name: /acme games/i }),
    ).toBeInTheDocument();
  });

  it("shows the loading state while fetching", () => {
    setHookState({ data: undefined, isLoading: true });
    render(<SuppliersPage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows the error state and allows retry", async () => {
    const refetch = vi.fn();
    setHookState({
      data: undefined,
      error: new Error("boom"),
      refetch,
    });
    render(<SuppliersPage />);

    const retry = screen.getByRole("button", { name: "Retry" });
    await userEvent.setup().click(retry);
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("shows the empty state when there are no suppliers", () => {
    setHookState({ data: [] });
    render(<SuppliersPage />);
    expect(screen.getByText("No suppliers yet")).toBeInTheDocument();
  });

  it("opens the create modal when the create button is clicked", async () => {
    const user = userEvent.setup();
    render(<SuppliersPage />);
    await user.click(
      screen.getByRole("button", { name: "Create Supplier" }),
    );
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
  });

  it("toggles favorite through the hook when the card action is used", async () => {
    const user = userEvent.setup();
    render(<SuppliersPage />);
    const favoriteButton = screen.getByRole("button", {
      name: "Mark as favorite",
    });
    await user.click(favoriteButton);
    expect(mockToggleFavorite.mutate).toHaveBeenCalledWith({
      id: "supplier-1",
      currentFavorite: false,
    });
  });

  it("supports keyboard activation of the create action", async () => {
    const user = userEvent.setup();
    render(<SuppliersPage />);
    const createButton = screen.getByRole("button", {
      name: "Create Supplier",
    });
    createButton.focus();
    expect(createButton).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
  });

  it("has no accessibility violations with a populated list", async () => {
    const { container } = render(<SuppliersPage />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations in the empty state", async () => {
    setHookState({ data: [] });
    const { container } = render(<SuppliersPage />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
