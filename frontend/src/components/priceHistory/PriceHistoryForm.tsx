import { useState, useId } from "react";
import { useTranslation } from "react-i18next";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type { PriceHistoryCreate } from "../../types/priceHistory";

interface PriceHistoryFormProps {
  onSubmit: (data: PriceHistoryCreate) => void;
  onCancel: () => void;
  isLoading: boolean;
}

/**
 * PriceHistoryForm - form to add a price record for a catalog item.
 * Validates condition non-empty, price >= 0, and a price date.
 */
export function PriceHistoryForm({
  onSubmit,
  onCancel,
  isLoading,
}: PriceHistoryFormProps) {
  const { t } = useTranslation();
  const formId = useId();

  const [condition, setCondition] = useState("");
  const [isComplete, setIsComplete] = useState(true);
  const [price, setPrice] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [source, setSource] = useState("");
  const [priceDate, setPriceDate] = useState("");
  const [region, setRegion] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!condition.trim()) {
      next.condition = t("errors.priceHistory.conditionRequired");
    }
    const priceNum = Number(price);
    if (price === "" || Number.isNaN(priceNum) || priceNum < 0) {
      next.price = t("errors.priceHistory.negativePrice");
    }
    if (!priceDate) {
      next.priceDate = t("errors.priceHistory.dateRequired");
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      condition: condition.trim(),
      isComplete,
      price,
      currency: currency || "USD",
      source: source || null,
      priceDate,
      region: region || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} aria-labelledby={`${formId}-title`}>
      <h3 id={`${formId}-title`} className="mb-3 text-lg font-semibold">
        {t("priceHistory.add")}
      </h3>
      <div className="space-y-3">
        <Input
          label={t("priceHistory.condition")}
          value={condition}
          onChange={(e) => setCondition(e.target.value)}
          error={errors.condition}
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isComplete}
            onChange={(e) => setIsComplete(e.target.checked)}
          />
          {t("priceHistory.isComplete")}
        </label>
        <Input
          label={t("priceHistory.price")}
          type="number"
          step="0.01"
          min="0"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          error={errors.price}
        />
        <Input
          label={t("priceHistory.currency")}
          value={currency}
          maxLength={3}
          onChange={(e) => setCurrency(e.target.value.toUpperCase())}
        />
        <Input
          label={t("priceHistory.source")}
          value={source}
          onChange={(e) => setSource(e.target.value)}
        />
        <Input
          label={t("priceHistory.priceDate")}
          type="date"
          value={priceDate}
          onChange={(e) => setPriceDate(e.target.value)}
          error={errors.priceDate}
        />
        <Input
          label={t("priceHistory.region")}
          value={region}
          onChange={(e) => setRegion(e.target.value)}
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
