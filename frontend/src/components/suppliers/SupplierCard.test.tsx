import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { SupplierCard } from "./SupplierCard";
import type { Supplier } from "../../types/supplier";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "common.edit": "Edit",
        "common.delete": "Delete",
        "suppliers.edit": "Edit supplier",
        "suppliers.delete": "Delete supplier",
        "suppliers.favorite": "Mark as favorite",
        "suppliers.typeOptions.online": "Online Store",
        "suppliers.typeOptions.store": "Store",
      };
      return translations[key] ?? key;
    },
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

function renderCard(overrides: Partial<Supplier> = {}) {
  const supplier = { ...baseSupplier, ...overrides };
  const onEdit = vi.fn();
  const onDelete = vi.fn();
  const onToggleFavorite = vi.fn();
  const utils = render(
    <SupplierCard
      supplier={supplier}
      onEdit={onEdit}
      onDelete={onDelete}
      onToggleFavorite={onToggleFavorite}
    />,
  );
  return { supplier, onEdit, onDelete, onToggleFavorite, ...utils };
}

describe("SupplierCard", () => {
  it("renders supplier name as a heading", () => {
    renderCard();
    expect(
      screen.getByRole("heading", { name: /acme games/i }),
    ).toBeInTheDocument();
  });

  it("associates the article with its heading via aria-labelledby", () => {
    const { supplier } = renderCard();
    const article = screen.getByRole("article", { name: /acme games/i });
    expect(article).toHaveAttribute("aria-labelledby", `supplier-${supplier.id}`);
  });

  it("renders the translated supplier type label", () => {
    renderCard({ type: "online" });
    expect(screen.getByText("Online Store")).toBeInTheDocument();
  });

  it("renders the combined location when city and country are present", () => {
    renderCard({ city: "New York", country: "US" });
    expect(screen.getByText("New York, US")).toBeInTheDocument();
  });

  it("renders the rating when provided", () => {
    renderCard({ rating: 4.5 });
    expect(screen.getByText("4.5 / 5.0")).toBeInTheDocument();
  });

  it("does not render rating when it is null", () => {
    renderCard({ rating: null });
    expect(screen.queryByText(/\/ 5\.0/)).not.toBeInTheDocument();
  });

  it("renders the website link with safe rel attributes", () => {
    renderCard({ website: "https://acme-games.example.com" });
    const link = screen.getByRole("link", {
      name: "https://acme-games.example.com",
    });
    expect(link).toHaveAttribute("href", "https://acme-games.example.com");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("calls onEdit with the supplier id when edit is clicked", async () => {
    const user = userEvent.setup();
    const { onEdit, supplier } = renderCard();
    await user.click(screen.getByRole("button", { name: "Edit supplier" }));
    expect(onEdit).toHaveBeenCalledWith(supplier.id);
  });

  it("calls onDelete with the supplier id when delete is clicked", async () => {
    const user = userEvent.setup();
    const { onDelete, supplier } = renderCard();
    await user.click(screen.getByRole("button", { name: "Delete supplier" }));
    expect(onDelete).toHaveBeenCalledWith(supplier.id);
  });

  it("calls onToggleFavorite with id and current favorite state", async () => {
    const user = userEvent.setup();
    const { onToggleFavorite, supplier } = renderCard({ isFavorite: false });
    await user.click(screen.getByRole("button", { name: "Mark as favorite" }));
    expect(onToggleFavorite).toHaveBeenCalledWith(supplier.id, false);
  });

  it("supports keyboard activation of the edit action", async () => {
    const user = userEvent.setup();
    const { onEdit } = renderCard();
    const editButton = screen.getByRole("button", { name: "Edit supplier" });
    editButton.focus();
    expect(editButton).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it("has no accessibility violations", async () => {
    const { container } = renderCard();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
