import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { ItemCard } from "./ItemCard";
import type { CollectionItem } from "../../types/item";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "items.condition": "Condition",
        "items.mint": "Mint",
        "items.nearMint": "Near Mint",
        "items.excellent": "Excellent",
        "items.good": "Good",
        "items.fair": "Fair",
        "items.poor": "Poor",
        "items.price": "Price",
        "items.edit": "Edit Item",
        "common.edit": "Edit",
      };
      return translations[key] ?? key;
    },
  }),
}));

const mockItem: CollectionItem = {
  id: "item-1",
  collectionId: "col-1",
  catalogItemId: "cat-item-1",
  condition: "excellent",
  isComplete: true,
  notes: null,
  purchasePrice: 45.0,
  purchaseCurrency: "USD",
  purchaseDate: null,
  acquisitionType: "purchase",
  storageLocation: null,
  supplierId: null,
  isAuthentic: true,
  authenticityNotes: null,
  countryOfOrigin: null,
  conditionNotes: null,
  customFields: null,
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
};

describe("ItemCard", () => {
  it("renders item condition", () => {
    render(<ItemCard item={mockItem} />);
    expect(screen.getByText(/Condition.*Excellent/)).toBeInTheDocument();
  });

  it("renders purchase price when present", () => {
    render(<ItemCard item={mockItem} />);
    expect(screen.getByText(/Price.*USD.*45/)).toBeInTheDocument();
  });

  it("does not render price when null", () => {
    const itemNoPrice = { ...mockItem, purchasePrice: null };
    render(<ItemCard item={itemNoPrice} />);
    expect(screen.queryByText(/Price/)).not.toBeInTheDocument();
  });

  it("renders as article with aria-labelledby", () => {
    render(<ItemCard item={mockItem} />);
    const article = screen.getByRole("article");
    expect(article).toHaveAttribute("aria-labelledby", "item-item-1");
  });

  it("renders primary image when provided", () => {
    const { container } = render(
      <ItemCard item={mockItem} primaryImageUrl="/uploads/test.jpg" />,
    );
    const img = container.querySelector("img");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "/uploads/test.jpg");
  });

  it("calls onEdit when edit button is clicked", async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    render(<ItemCard item={mockItem} onEdit={onEdit} />);
    await user.click(screen.getByRole("button", { name: "Edit Item" }));
    expect(onEdit).toHaveBeenCalledWith("item-1");
  });

  it("does not render edit button when onEdit is not provided", () => {
    render(<ItemCard item={mockItem} />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<ItemCard item={mockItem} onEdit={vi.fn()} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
