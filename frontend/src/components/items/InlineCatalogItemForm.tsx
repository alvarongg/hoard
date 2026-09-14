import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCreateCatalogItem } from "../../hooks/useCreateCatalogItem";
import type { CatalogItem, CatalogItemCreate } from "../../types/item";
import { Button } from "../ui/Button";
import { ErrorMessage } from "../ui/ErrorMessage";
import { Input } from "../ui/Input";

interface InlineCatalogItemFormProps {
  catalogId: string;
  onCreated: (item: CatalogItem) => void;
  onCancel: () => void;
  isLoading: boolean;
}

type OptionalField =
  | "subtitle"
  | "description"
  | "manufacturer"
  | "publisher"
  | "developer"
  | "brand"
  | "language"
  | "region"
  | "rarity";

const OPTIONAL_FIELDS: OptionalField[] = [
  "subtitle",
  "description",
  "manufacturer",
  "publisher",
  "developer",
  "brand",
  "language",
  "region",
  "rarity",
];

const EMPTY_OPTIONAL_VALUES: Record<OptionalField, string> = {
  subtitle: "",
  description: "",
  manufacturer: "",
  publisher: "",
  developer: "",
  brand: "",
  language: "",
  region: "",
  rarity: "",
};

function buildPayload(
  title: string,
  optionalValues: Record<OptionalField, string>,
): CatalogItemCreate {
  const payload: CatalogItemCreate = { title: title.trim() };

  for (const field of OPTIONAL_FIELDS) {
    const value = optionalValues[field].trim();
    if (value) payload[field] = value;
  }

  return payload;
}

export function InlineCatalogItemForm({
  catalogId,
  onCreated,
  onCancel,
  isLoading,
}: InlineCatalogItemFormProps) {
  const { t } = useTranslation();
  const headingId = useId();
  const optionalFieldsId = useId();
  const titleInputId = useId();

  const [title, setTitle] = useState("");
  const [optionalValues, setOptionalValues] = useState(EMPTY_OPTIONAL_VALUES);
  const [showOptional, setShowOptional] = useState(false);
  const [titleError, setTitleError] = useState<string>();

  const { mutate, isPending, error, reset } = useCreateCatalogItem(catalogId);
  const isSubmitting = isLoading || isPending;

  useEffect(() => {
    document.getElementById(titleInputId)?.focus();
  }, [titleInputId]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      onCancel();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  function validate(): boolean {
    if (!title) {
      setTitleError(t("items.inline.titleRequired"));
      return false;
    }
    if (!title.trim()) {
      setTitleError(t("items.inline.titleWhitespace"));
      return false;
    }

    setTitleError(undefined);
    return true;
  }

  function handleSubmit() {
    reset();
    if (!validate()) return;

    mutate(buildPayload(title, optionalValues), {
      onSuccess: (item) => onCreated(item),
    });
  }

  function handleTitleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    handleSubmit();
  }

  function updateOptional(field: OptionalField, value: string) {
    setOptionalValues((previous) => ({ ...previous, [field]: value }));
  }

  return (
    <section
      aria-labelledby={headingId}
      className="space-y-4 rounded-md border border-gray-200 bg-gray-50 p-4"
    >
      <h3 id={headingId} className="text-sm font-semibold text-gray-800">
        {t("items.inline.createNew")}
      </h3>

      <Input
        id={titleInputId}
        label={t("items.inline.title")}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={handleTitleKeyDown}
        error={titleError}
        required
        aria-required="true"
        maxLength={500}
      />

      <div>
        <button
          type="button"
          onClick={() => setShowOptional((previous) => !previous)}
          aria-expanded={showOptional}
          aria-controls={optionalFieldsId}
          className="text-sm font-medium text-blue-600 underline hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {showOptional
            ? t("items.inline.hideOptional")
            : t("items.inline.showOptional")}
        </button>

        <div
          id={optionalFieldsId}
          hidden={!showOptional}
          role="group"
          aria-label={t("items.inline.optionalFields")}
          className="mt-3 space-y-3"
        >
          {OPTIONAL_FIELDS.map((field) => (
            <Input
              key={field}
              label={t(`items.inline.${field}`)}
              value={optionalValues[field]}
              onChange={(e) => updateOptional(field, e.target.value)}
            />
          ))}
        </div>
      </div>

      <div aria-live="polite" className="sr-only">
        {isSubmitting ? t("items.inline.creating") : ""}
      </div>

      {error && <ErrorMessage message={t("items.inline.createError")} />}

      <div className="flex gap-2">
        <Button type="button" onClick={handleSubmit} isLoading={isSubmitting}>
          {t("common.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </section>
  );
}
