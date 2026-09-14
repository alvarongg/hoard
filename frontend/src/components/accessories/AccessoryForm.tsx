import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type { Accessory, AccessoryCreate } from "../../types/accessory";

interface AccessoryFormProps {
  initialData?: Accessory | null;
  onSubmit: (data: AccessoryCreate) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export function AccessoryForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}: AccessoryFormProps) {
  const { t } = useTranslation();
  const [name, setName] = useState(initialData?.name ?? "");
  const [category, setCategory] = useState(initialData?.category ?? "");
  const [quantityTotal, setQuantityTotal] = useState(
    String(initialData?.quantityTotal ?? 0),
  );
  const [minimumStockAlert, setMinimumStockAlert] = useState(
    String(initialData?.minimumStockAlert ?? 5),
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!name.trim()) next.name = t("errors.accessory.nameRequired");
    if (Number(quantityTotal) < 0) {
      next.quantityTotal = t("errors.accessory.invalidStock");
    }
    setErrors(next);
    if (Object.keys(next).length > 0) return;
    onSubmit({
      name: name.trim(),
      category: category || null,
      quantityTotal: Number(quantityTotal),
      minimumStockAlert: Number(minimumStockAlert),
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-3">
        <Input
          label={t("accessories.name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
        />
        <Input
          label={t("accessories.category")}
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
        <Input
          label={t("accessories.quantityTotal")}
          type="number"
          min="0"
          value={quantityTotal}
          onChange={(e) => setQuantityTotal(e.target.value)}
          error={errors.quantityTotal}
        />
        <Input
          label={t("accessories.minimumStockAlert")}
          type="number"
          min="0"
          value={minimumStockAlert}
          onChange={(e) => setMinimumStockAlert(e.target.value)}
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
