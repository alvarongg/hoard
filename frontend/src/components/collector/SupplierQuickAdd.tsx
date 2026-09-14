import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useQuickAddSupplier } from "../../hooks/useCollectorWorkflow";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

interface SupplierQuickAddProps {
  onCreated: (supplierId: string) => void;
  onCancel: () => void;
}

export function SupplierQuickAdd({
  onCreated,
  onCancel,
}: SupplierQuickAddProps) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [country, setCountry] = useState("");
  const quickAdd = useQuickAddSupplier();

  const handleCreate = () => {
    if (!name.trim()) return;
    quickAdd.mutate(
      { name: name.trim(), country: country.trim() || null },
      { onSuccess: (supplier) => onCreated(supplier.id) },
    );
  };

  return (
    <fieldset className="rounded border border-gray-300 p-3">
      <legend className="px-1 text-sm font-medium">
        {t("collector.supplierQuickAdd.title")}
      </legend>
      <div className="flex flex-col gap-2">
        <Input
          label={t("collector.supplierQuickAdd.name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Input
          label={t("collector.supplierQuickAdd.country")}
          value={country}
          maxLength={2}
          placeholder="JP"
          onChange={(e) => setCountry(e.target.value.toUpperCase())}
        />
        <div className="flex gap-2">
          <Button
            type="button"
            onClick={handleCreate}
            disabled={!name.trim() || quickAdd.isPending}
          >
            {t("collector.supplierQuickAdd.create")}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel}>
            {t("common.cancel")}
          </Button>
        </div>
        {quickAdd.isError && (
          <p className="text-sm text-red-600">
            {t("collector.supplierQuickAdd.error")}
          </p>
        )}
      </div>
    </fieldset>
  );
}
