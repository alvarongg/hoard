import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { TransactionList } from "./TransactionList";
import { InvestmentSummary } from "./InvestmentSummary";
import { TransactionForm } from "./TransactionForm";
import type { Transaction, ItemInvestment } from "../../types/transaction";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      if (key === "transactions.deleteEntry" && opts?.date) {
        return `Delete transaction from ${String(opts.date)}`;
      }
      const map: Record<string, string> = {
        "transactions.title": "Transactions",
        "transactions.empty": "No transactions",
        "transactions.add": "Add transaction",
        "transactions.date": "Date",
        "transactions.amount": "Amount",
        "transactions.shippingCost": "Shipping",
        "transactions.taxAmount": "Tax",
        "transactions.otherFees": "Other fees",
        "transactions.totalAmount": "Total",
        "transactions.currency": "Currency",
        "transactions.type.label": "Type",
        "transactions.type.purchase": "Purchase",
        "transactions.type.sale": "Sale",
        "transactions.type.trade_in": "Trade in",
        "transactions.type.trade_out": "Trade out",
        "transactions.type.gift_received": "Gift received",
        "transactions.type.gift_given": "Gift given",
        "transactions.type.grading_fee": "Grading fee",
        "transactions.type.repair": "Repair",
        "transactions.type.appraisal": "Appraisal",
        "transactions.type.other": "Other",
        "transactions.investment.title": "Investment",
        "transactions.investment.realInvested": "Real invested",
        "transactions.investment.totalOutflow": "Outflow",
        "transactions.investment.totalInflow": "Inflow",
        "transactions.investment.roi": "ROI",
        "transactions.investment.roiUnavailable": "no data",
        "errors.transaction.dateRequired": "Date is required",
        "common.actions": "Actions",
        "common.delete": "Delete",
        "common.save": "Save",
        "common.saving": "Saving",
        "common.cancel": "Cancel",
      };
      return map[key] ?? key;
    },
  }),
}));

const tx: Transaction = {
  id: "t1",
  collectionItemId: "ci1",
  transactionType: "purchase",
  transactionDate: "2026-03-01",
  amount: "100.00",
  currency: "USD",
  shippingCost: "10.00",
  taxAmount: null,
  otherFees: null,
  totalAmount: "110.00",
  supplierId: null,
  counterpartName: null,
  invoiceNumber: null,
  receiptPath: null,
  paymentMethod: null,
  notes: null,
  createdAt: "2026-03-01T00:00:00Z",
};

describe("TransactionList", () => {
  it("renders rows with total", () => {
    render(<TransactionList transactions={[tx]} />);
    expect(screen.getByText("110.00 USD")).toBeInTheDocument();
    expect(screen.getByText("Purchase")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<TransactionList transactions={[]} />);
    expect(screen.getByText("No transactions")).toBeInTheDocument();
  });

  it("calls onDelete", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(<TransactionList transactions={[tx]} onDelete={onDelete} />);
    await user.click(
      screen.getByRole("button", { name: /delete transaction from/i }),
    );
    expect(onDelete).toHaveBeenCalledWith("t1");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<TransactionList transactions={[tx]} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("InvestmentSummary", () => {
  it("renders ROI value", () => {
    const inv: ItemInvestment = {
      realInvested: "100.00",
      totalOutflow: "100.00",
      totalInflow: "0",
      currentMarketValue: "150.00",
      roiPercentage: "50.00",
      source: "transactions",
    };
    render(<InvestmentSummary investment={inv} />);
    expect(screen.getByText("50.00%")).toBeInTheDocument();
  });

  it("renders null ROI as explanatory text, not 0", () => {
    const inv: ItemInvestment = {
      realInvested: "0",
      totalOutflow: "100.00",
      totalInflow: "100.00",
      currentMarketValue: "150.00",
      roiPercentage: null,
      source: "transactions",
    };
    render(<InvestmentSummary investment={inv} />);
    expect(screen.getByText("no data")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const inv: ItemInvestment = {
      realInvested: "0",
      totalOutflow: "0",
      totalInflow: "0",
      currentMarketValue: null,
      roiPercentage: null,
      source: "purchase_price",
    };
    const { container } = render(<InvestmentSummary investment={inv} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("TransactionForm", () => {
  it("shows a live derived total", async () => {
    const user = userEvent.setup();
    render(
      <TransactionForm onSubmit={vi.fn()} onCancel={vi.fn()} isLoading={false} />,
    );
    await user.type(screen.getByLabelText("Amount"), "100");
    await user.type(screen.getByLabelText("Shipping"), "10");
    const total = screen.getByLabelText("Total");
    expect(total.textContent).toContain("110.00");
  });

  it("requires a date", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <TransactionForm
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        isLoading={false}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("Date is required")).toBeInTheDocument();
  });

  it("submits with valid data", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(
      <TransactionForm
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        isLoading={false}
      />,
    );
    await user.type(screen.getByLabelText("Date"), "2026-03-01");
    await user.type(screen.getByLabelText("Amount"), "100");
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        transactionType: "purchase",
        transactionDate: "2026-03-01",
        amount: "100",
      }),
    );
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <TransactionForm onSubmit={vi.fn()} onCancel={vi.fn()} isLoading={false} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
