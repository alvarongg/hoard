import { useState, useId } from "react";
import { useTranslation } from "react-i18next";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";
import type {
  TransactionCreate,
  TransactionType,
} from "../../types/transaction";

interface TransactionFormProps {
  onSubmit: (data: TransactionCreate) => void;
  onCancel: () => void;
  isLoading: boolean;
}

const TYPES: TransactionType[] = [
  "purchase",
  "sale",
  "trade_in",
  "trade_out",
  "gift_received",
  "gift_given",
  "grading_fee",
  "repair",
  "appraisal",
  "other",
];

function toNum(v: string): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

/**
 * TransactionForm - create an item transaction.
 * total_amount is server-computed; a live read-only preview is shown here.
 */
export function TransactionForm({
  onSubmit,
  onCancel,
  isLoading,
}: TransactionFormProps) {
  const { t } = useTranslation();
  const formId = useId();

  const [transactionType, setTransactionType] =
    useState<TransactionType>("purchase");
  const [transactionDate, setTransactionDate] = useState("");
  const [amount, setAmount] = useState("");
  const [shippingCost, setShippingCost] = useState("");
  const [taxAmount, setTaxAmount] = useState("");
  const [otherFees, setOtherFees] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const liveTotal = (
    toNum(amount) + toNum(shippingCost) + toNum(taxAmount) + toNum(otherFees)
  ).toFixed(2);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!transactionDate) {
      next.transactionDate = t("errors.transaction.dateRequired");
    }
    setErrors(next);
    if (Object.keys(next).length > 0) return;
    onSubmit({
      transactionType,
      transactionDate,
      amount: amount || null,
      shippingCost: shippingCost || null,
      taxAmount: taxAmount || null,
      otherFees: otherFees || null,
      currency: currency || "USD",
    });
  }

  return (
    <form onSubmit={handleSubmit} aria-labelledby={`${formId}-title`}>
      <h3 id={`${formId}-title`} className="mb-3 text-lg font-semibold">
        {t("transactions.add")}
      </h3>
      <div className="space-y-3">
        <Select
          label={t("transactions.type.label")}
          value={transactionType}
          onChange={(e) =>
            setTransactionType(e.target.value as TransactionType)
          }
          options={TYPES.map((tt) => ({
            value: tt,
            label: t(`transactions.type.${tt}`),
          }))}
        />
        <Input
          label={t("transactions.date")}
          type="date"
          value={transactionDate}
          onChange={(e) => setTransactionDate(e.target.value)}
          error={errors.transactionDate}
        />
        <Input
          label={t("transactions.amount")}
          type="number"
          step="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <Input
          label={t("transactions.shippingCost")}
          type="number"
          step="0.01"
          value={shippingCost}
          onChange={(e) => setShippingCost(e.target.value)}
        />
        <Input
          label={t("transactions.taxAmount")}
          type="number"
          step="0.01"
          value={taxAmount}
          onChange={(e) => setTaxAmount(e.target.value)}
        />
        <Input
          label={t("transactions.otherFees")}
          type="number"
          step="0.01"
          value={otherFees}
          onChange={(e) => setOtherFees(e.target.value)}
        />
        <div>
          <span className="text-sm font-medium text-gray-700">
            {t("transactions.totalAmount")}
          </span>
          <output
            aria-label={t("transactions.totalAmount")}
            className="ml-2 text-sm font-semibold text-gray-900 dark:text-white"
          >
            {liveTotal} {currency}
          </output>
        </div>
        <Input
          label={t("transactions.currency")}
          value={currency}
          maxLength={3}
          onChange={(e) => setCurrency(e.target.value.toUpperCase())}
        />
      </div>
      <div className="mt-4 flex gap-2">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? t("common.saving") : t("common.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </form>
  );
}
