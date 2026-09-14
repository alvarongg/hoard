import { useState } from "react";
import { useTranslation } from "react-i18next";

import type {
  CollectionItem,
  CollectionItemUpdate,
  ItemCondition,
} from "../../types/item";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";

const CONDITIONS: ItemCondition[] = [
  "mint",
  "near_mint",
  "excellent",
  "good",
  "fair",
  "poor",
];

interface CollectionItemEditFormProps {
  item: CollectionItem;
  onSubmit: (data: CollectionItemUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function CollectionItemEditForm({
  item,
  onSubmit,
  onCancel,
  isLoading = false,
}: CollectionItemEditFormProps) {
  const { t } = useTranslation();
  const [condition, setCondition] = useState<ItemCondition>(item.condition);
  const [notes, setNotes] = useState(item.notes ?? "");
  const [conditionNotes, setConditionNotes] = useState(
    item.conditionNotes ?? "",
  );
  const [price, setPrice] = useState(
    item.purchasePrice != null ? String(item.purchasePrice) : "",
  );
  const [storageLocation, setStorageLocation] = useState(
    item.storageLocation ?? "",
  );
  const [countryOfOrigin, setCountryOfOrigin] = useState(
    item.countryOfOrigin ?? "",
  );
  const [isAuthentic, setIsAuthentic] = useState(item.isAuthentic);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      condition,
      notes: notes.trim() || undefined,
      conditionNotes: conditionNotes.trim() || undefined,
      purchasePrice: price.trim() ? Number(price) : undefined,
      storageLocation: storageLocation.trim() || undefined,
      countryOfOrigin: countryOfOrigin.trim().toUpperCase() || undefined,
      isAuthentic,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Select
        label={t("collector.addToCollection.condition")}
        value={condition}
        onChange={(e) => setCondition(e.target.value as ItemCondition)}
        options={CONDITIONS.map((c) => ({
          value: c,
          label: t(`items.${c === "near_mint" ? "nearMint" : c}`),
        }))}
      />
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={!isAuthentic}
          onChange={(e) => setIsAuthentic(!e.target.checked)}
        />
        {t("collector.addToCollection.bootleg")}
      </label>
      <Input
        label={t("collector.addToCollection.country")}
        value={countryOfOrigin}
        maxLength={2}
        onChange={(e) => setCountryOfOrigin(e.target.value.toUpperCase())}
      />
      <Input
        label={t("collector.addToCollection.price")}
        type="number"
        min="0"
        step="0.01"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
      />
      <Input
        label={t("collector.addToCollection.storageLocation")}
        value={storageLocation}
        onChange={(e) => setStorageLocation(e.target.value)}
      />
      <Input
        label={t("items.notes")}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
      <Input
        label={t("collector.addToCollection.conditionNotes")}
        value={conditionNotes}
        onChange={(e) => setConditionNotes(e.target.value)}
      />
      <div className="flex gap-2">
        <Button type="submit" disabled={isLoading}>
          {t("common.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </form>
  );
}
