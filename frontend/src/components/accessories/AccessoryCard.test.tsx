import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { StockBadge } from "./StockBadge";
import { AccessoryCard } from "./AccessoryCard";
import { LowStockList } from "./LowStockList";
import type { Accessory, LowStockEntry } from "../../types/accessory";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "accessories.lowStock") return `Low stock: ${opts?.count}`;
      if (key === "accessories.inStock") return `In stock: ${opts?.count}`;
      if (key === "accessories.suggestedReorder")
        return `Avail. ${opts?.available} reorder ${opts?.reorder}`;
      const map: Record<string, string> = {
        "accessories.quantityTotal": "Total quantity",
        "accessories.quantityInUse": "In use",
        "accessories.quantityAvailable": "Available",
        "accessories.lowStockTitle": "Low stock",
        "accessories.noLowStock": "No stock alerts",
        "common.edit": "Edit",
        "common.delete": "Delete",
      };
      return map[key] ?? key;
    },
  }),
}));

const acc: Accessory = {
  id: "a1",
  name: "Plastic Case",
  category: "protection",
  subcategory: null,
  compatibleSubCategories: null,
  sizeSpecifications: null,
  quantityTotal: 10,
  quantityInUse: 3,
  quantityAvailable: 7,
  isLowStock: false,
  minimumStockAlert: 5,
  reorderQuantity: 20,
  unitCost: null,
  currency: "USD",
  supplierId: null,
  supplierSku: null,
  supplierUrl: null,
  notes: null,
};

describe("StockBadge", () => {
  it("shows text, not only color, for low stock", () => {
    render(<StockBadge quantityAvailable={2} isLowStock={true} />);
    expect(screen.getByText("Low stock: 2")).toBeInTheDocument();
  });

  it("shows in-stock text", () => {
    render(<StockBadge quantityAvailable={7} isLowStock={false} />);
    expect(screen.getByText("In stock: 7")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <StockBadge quantityAvailable={2} isLowStock={true} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("AccessoryCard", () => {
  it("renders stock figures and triggers actions", async () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(
      <AccessoryCard accessory={acc} onEdit={onEdit} onDelete={onDelete} />,
    );
    expect(screen.getByText("Plastic Case")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Edit" }));
    expect(onEdit).toHaveBeenCalledWith(acc);
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(onDelete).toHaveBeenCalledWith("a1");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<AccessoryCard accessory={acc} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("LowStockList", () => {
  const entries: LowStockEntry[] = [
    {
      id: "a1",
      name: "Case",
      quantityAvailable: 2,
      minimumStockAlert: 5,
      reorderQuantity: 20,
    },
  ];

  it("lists low-stock accessories", () => {
    render(<LowStockList entries={entries} />);
    expect(screen.getByText("Case")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<LowStockList entries={[]} />);
    expect(screen.getByText("No stock alerts")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<LowStockList entries={entries} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
