import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

interface CatalogQuickAddProps {
  onCreate: (name: string, tematica: string) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function CatalogQuickAdd({
  onCreate,
  onCancel,
  isLoading = false,
}: CatalogQuickAddProps) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [tematica, setTematica] = useState("");

  return (
    <fieldset className="rounded border border-gray-300 p-3">
      <legend className="px-1 text-sm font-medium">
        {t("collector.catalogQuickAdd.title")}
      </legend>
      <div className="flex flex-col gap-2">
        <Input
          label={t("collector.catalogQuickAdd.name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <Input
          label={t("collector.catalogQuickAdd.tematica")}
          value={tematica}
          onChange={(e) => setTematica(e.target.value)}
          required
        />
        <div className="flex gap-2">
          <Button
            type="button"
            onClick={() => onCreate(name.trim(), tematica.trim())}
            disabled={!name.trim() || !tematica.trim() || isLoading}
          >
            {t("collector.catalogQuickAdd.create")}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel}>
            {t("common.cancel")}
          </Button>
        </div>
      </div>
    </fieldset>
  );
}
