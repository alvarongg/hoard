import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { PriceHistoryTable } from "./PriceHistoryTable";
import { LatestPriceSummary } from "./LatestPriceSummary";
import { PriceHistoryForm } from "./PriceHistoryForm";
import type {
  PriceHistoryEntry,
  LatestPriceEntry,
} from "../../types/priceHistory";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "priceHistory.deleteEntry" && opts?.date) {
        return `Delete price from ${String(opts.date)}`;
      }
      const map: Record<string, string> = {
        "priceHistory.title": "Price history",
        "priceHistory.empty": "No price history",
        "priceHistory.priceDate": "Date",
        "priceHistory.condition": "Condition",
        "priceHistory.isComplete": "Complete",
        "priceHistory.price": "Price",
        "priceHistory.currency": "Currency",
        "priceHistory.source": "Source",
        "priceHistory.region": "Region",
        "priceHistory.latest": "Latest prices",
        "priceHistory.add": "Add price",
        "priceHistory.incompleteShort": "incomplete",
        "common.yes": "Yes",
        "common.no": "No",
        "common.actions": "Actions",
        "common.delete": "Delete",
        "common.save": "Save",
        "common.saving": "Saving",
        "common.cancel": "Cancel",
        "errors.priceHistory.conditionRequired": "Condition is required",
        "errors.priceHistory.negativePrice": "Price must be 0 or greater",
        "errors.priceHistory.dateRequired": "Date is required",
        "table.sortAscending": "Sort ascending",
        "table.sortDescending": "Sort descending",
      };
      return map[key] ?? key;
    },
  }),
}));

const entries: PriceHistoryEntry[] = [
  {
    id: "ph-1",
    catalogItemId: "c1",
    condition: "good",
    isComplete: true,
    completenessDescription: null,
    price: "50.00",
    currency: "USD",
    source: "eBay",
    sourceUrl: null,
    priceDate: "2026-03-01",
    region: null,
    notes: null,
    recordedAt: "2026-03-01T00:00:00Z",
  },
];

describe("PriceHistoryTable", () => {
  it("renders rows", () => {
    render(<PriceHistoryTable entries={entries} />);
    expect(screen.getByText("2026-03-01")).toBeInTheDocument();
    expect(screen.getByText("50.00 USD")).toBeInTheDocument();
  });

  it("shows empty state with no entries", () => {
    render(<PriceHistoryTable entries={[]} />);
    expect(screen.getByText("No price history")).toBeInTheDocument();
  });

  it("calls onDelete", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(<PriceHistoryTable entries={entries} onDelete={onDelete} />);
    await user.click(screen.getByRole("button", { name: /delete price from/i }));
    expect(onDelete).toHaveBeenCalledWith("ph-1");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<PriceHistoryTable entries={entries} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("LatestPriceSummary", () => {
  const latest: LatestPriceEntry[] = [
    {
      condition: "good",
      isComplete: true,
      price: "50.00",
      currency: "USD",
      priceDate: "2026-03-01",
      source: "eBay",
    },
  ];

  it("renders latest prices", () => {
    render(<LatestPriceSummary entries={latest} />);
    expect(screen.getByText("50.00 USD")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<LatestPriceSummary entries={[]} />);
    expect(screen.getByText("No price history")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<LatestPriceSummary entries={latest} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("PriceHistoryForm", () => {
  it("validates required fields", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <PriceHistoryForm onSubmit={onSubmit} onCancel={vi.fn()} isLoading={false} />,
    );
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("Condition is required")).toBeInTheDocument();
  });

  it("submits valid data", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <PriceHistoryForm onSubmit={onSubmit} onCancel={vi.fn()} isLoading={false} />,
    );
    await user.type(screen.getByLabelText("Condition"), "good");
    await user.type(screen.getByLabelText("Price"), "50");
    await user.type(screen.getByLabelText("Date"), "2026-03-01");
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        condition: "good",
        price: "50",
        priceDate: "2026-03-01",
      }),
    );
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <PriceHistoryForm onSubmit={vi.fn()} onCancel={vi.fn()} isLoading={false} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
