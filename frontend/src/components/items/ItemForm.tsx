import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { CatalogItem, ItemCondition } from "../../types/item";
import { Select } from "../ui/Select";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

interface ItemFormData {
  catalogItemId: string;
  condition: ItemCondition;
  notes: string;
  purchasePrice: string;
}

interface ItemFormProps {
  catalogItems: CatalogItem[];
  onSubmit: (data: ItemFormData) => void;
  onCancel: () => void;
  isLoading: boolean;
}

const CONDITIONS: ItemCondition[] = [
  "mint",
  "near_mint",
  "excellent",
  "good",
  "fair",
  "poor",
];

const CONDITION_LABELS: Record<ItemCondition, string> = {
  mint: "items.mint",
  near_mint: "items.nearMint",
  excellent: "items.excellent",
  good: "items.good",
  fair: "items.fair",
  poor: "items.poor",
};

export function ItemForm({
  catalogItems,
  onSubmit,
  onCancel,
  isLoading,
}: ItemFormProps) {
  const { t } = useTranslation();

  const [catalogItemId, setCatalogItemId] = useState("");
  const [condition, setCondition] = useState("");
  const [notes, setNotes] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!catalogItemId) {
      newErrors.catalogItem = t("items.form.catalogItemRequired");
    }
    if (!condition) {
      newErrors.condition = t("items.form.conditionRequired");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!validate()) return;

    onSubmit({
      catalogItemId,
      condition: condition as ItemCondition,
      notes,
      purchasePrice,
    });
  }

  const catalogItemOptions = catalogItems.map((ci) => ({
    value: ci.id,
    label: ci.title,
  }));

  const conditionOptions = CONDITIONS.map((c) => ({
    value: c,
    label: t(CONDITION_LABELS[c]),
  }));

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <Select
        label={t("items.catalogItem")}
        options={catalogItemOptions}
        value={catalogItemId}
        onChange={(e) => setCatalogItemId(e.target.value)}
        placeholder={t("items.form.selectCatalogItem")}
        error={errors.catalogItem}
      />

      <Select
        label={t("items.condition")}
        options={conditionOptions}
        value={condition}
        onChange={(e) => setCondition(e.target.value)}
        placeholder={t("items.form.selectCondition")}
        error={errors.condition}
      />

      <Input
        label={t("items.notes")}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      <Input
        label={t("items.price")}
        type="number"
        min="0"
        step="0.01"
        value={purchasePrice}
        onChange={(e) => setPurchasePrice(e.target.value)}
      />

      <div className="flex gap-2 pt-2">
        <Button type="submit" isLoading={isLoading}>
          {t("common.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </form>
  );
}
