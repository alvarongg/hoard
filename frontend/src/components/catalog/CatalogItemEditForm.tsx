import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { CatalogItem } from "../../types/item";
import type { CatalogItemUpdate } from "../../hooks/useUpdateCatalogItem";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

interface CatalogItemEditFormProps {
  item: CatalogItem;
  onSubmit: (data: CatalogItemUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function CatalogItemEditForm({
  item,
  onSubmit,
  onCancel,
  isLoading = false,
}: CatalogItemEditFormProps) {
  const { t } = useTranslation();
  const [title, setTitle] = useState(item.title);
  const [description, setDescription] = useState(item.description ?? "");
  const [region, setRegion] = useState(item.region ?? "");
  const [manufacturer, setManufacturer] = useState(item.manufacturer ?? "");
  const [publisher, setPublisher] = useState(item.publisher ?? "");
  const [developer, setDeveloper] = useState(item.developer ?? "");
  const [variation, setVariation] = useState(item.variation ?? "");
  const [variationDetails, setVariationDetails] = useState(
    item.variationDetails ?? "",
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      title: title.trim(),
      description: description.trim() || null,
      region: region.trim() || null,
      manufacturer: manufacturer.trim() || null,
      publisher: publisher.trim() || null,
      developer: developer.trim() || null,
      variation: variation.trim() || null,
      variationDetails: variationDetails.trim() || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Input
        label={t("catalogItemEdit.title")}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />
      <Input
        label={t("catalogItemEdit.description")}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="flex gap-2">
        <Input
          label={t("catalogItemEdit.region")}
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        />
        <Input
          label={t("catalogItemEdit.manufacturer")}
          value={manufacturer}
          onChange={(e) => setManufacturer(e.target.value)}
        />
      </div>
      <div className="flex gap-2">
        <Input
          label={t("catalogItemEdit.publisher")}
          value={publisher}
          onChange={(e) => setPublisher(e.target.value)}
        />
        <Input
          label={t("catalogItemEdit.developer")}
          value={developer}
          onChange={(e) => setDeveloper(e.target.value)}
        />
      </div>
      <Input
        label={t("catalogItemEdit.variation")}
        value={variation}
        placeholder={t("catalogItemEdit.variationPlaceholder")}
        onChange={(e) => setVariation(e.target.value)}
      />
      <Input
        label={t("catalogItemEdit.variationDetails")}
        value={variationDetails}
        onChange={(e) => setVariationDetails(e.target.value)}
      />
      <div className="flex gap-2">
        <Button type="submit" disabled={isLoading || !title.trim()}>
          {t("common.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </form>
  );
}
