import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { WishlistCard } from "./WishlistCard";
import type { WishlistItem } from "../../types/wishlist";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "common.edit": "Edit",
        "common.delete": "Delete",
        "common.view": "View",
        "wishlist.viewDetails": "View details",
        "wishlist.edit": "Edit wishlist item",
        "wishlist.delete": "Delete wishlist item",
        "wishlist.budget": "Budget",
        "wishlist.condition": "Condition",
        "wishlist.mustBeComplete": "Must be complete",
        "wishlist.acquired": "Acquired",
        "wishlist.inactive": "Inactive",
        "wishlist.itemTitle": `Wishlist Item #${params?.id ?? ""}`,
        "wishlist.priority.critical": "Critical",
        "wishlist.priority.high": "High",
        "wishlist.priority.medium": "Medium",
        "wishlist.priority.low": "Low",
        "wishlist.priority.lowest": "Lowest",
        "wishlist.urgency.critical": "Critical",
        "wishlist.urgency.high": "High",
        "wishlist.urgency.medium": "Medium",
        "wishlist.urgency.low": "Low",
      };
      return translations[key] ?? key;
    },
  }),
}));

const baseItem: WishlistItem = {
  id: "item-1",
  collectionId: "coll-1",
  catalogItemId: "cat-1",
  priority: 3,
  urgency: "medium",
  maxPrice: 100,
  currency: "USD",
  desiredCondition: "Good",
  desiredConditionMin: null,
  mustBeComplete: true,
  desiredCompletenessDescription: null,
  specificVariantRequired: false,
  variantDescription: null,
  notes: null,
  searchNotes: null,
  tags: null,
  isActive: true,
  isAcquired: false,
  acquiredDate: null,
  acquiredCollectionItemId: null,
  createdAt: "2024-01-01T00:00:00",
  updatedAt: "2024-01-01T00:00:00",
};

function renderCard(overrides: Partial<WishlistItem> = {}) {
  const item = { ...baseItem, ...overrides };
  const onEdit = vi.fn();
  const onDelete = vi.fn();
  const onView = vi.fn();
  const utils = render(
    <WishlistCard item={item} onEdit={onEdit} onDelete={onDelete} onView={onView} />,
    { wrapper: MemoryRouter },
  );
  return { item, onEdit, onDelete, onView, ...utils };
}

describe("WishlistCard", () => {
  it("renders wishlist item heading", () => {
    renderCard();
    expect(screen.getByRole("heading")).toBeInTheDocument();
  });

  it("renders priority badge", () => {
    renderCard({ priority: 2 });
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("renders urgency badge", () => {
    renderCard({ urgency: "high" });
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("renders budget when present", () => {
    renderCard({ maxPrice: 100, currency: "USD" });
    expect(screen.getByText("$100.00")).toBeInTheDocument();
  });

  it("renders condition when present", () => {
    renderCard({ desiredCondition: "Good" });
    expect(screen.getByText("Good")).toBeInTheDocument();
  });

  it("renders must be complete indicator", () => {
    renderCard({ mustBeComplete: true });
    expect(screen.getByText("Must be complete")).toBeInTheDocument();
  });

  it("renders notes when present", () => {
    renderCard({ notes: "Looking for boxed version" });
    expect(screen.getByText("Looking for boxed version")).toBeInTheDocument();
  });

  it("renders acquired badge when item is acquired", () => {
    renderCard({ isAcquired: true });
    expect(screen.getByText("Acquired")).toBeInTheDocument();
  });

  it("renders inactive badge when item is not active", () => {
    renderCard({ isActive: false });
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("calls onEdit when edit button clicked", async () => {
    const user = userEvent.setup();
    const { onEdit, item } = renderCard();

    await user.click(screen.getByRole("button", { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledWith(item.id);
  });

  it("calls onDelete when delete button clicked", async () => {
    const user = userEvent.setup();
    const { onDelete, item } = renderCard();

    await user.click(screen.getByRole("button", { name: /delete/i }));
    expect(onDelete).toHaveBeenCalledWith(item.id);
  });

  it("calls onView when view button clicked", async () => {
    const user = userEvent.setup();
    const { onView, item } = renderCard();

    await user.click(screen.getByRole("link", { name: /view/i }));
    expect(onView).toHaveBeenCalledWith(item.id);
  });

  it("applies acquired styling when item is acquired", () => {
    renderCard({ isAcquired: true });

    const article = screen.getByRole("article");
    expect(article).toHaveClass("bg-green-50");
  });

  it("has no accessibility violations", async () => {
    const { container } = renderCard();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
