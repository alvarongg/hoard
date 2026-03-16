import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import type { CollectionType } from "../../types/collection";
import type { MainCategory, SubCategory } from "../../types/category";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";

interface CollectionFormData {
  name: string;
  description: string;
  collectionType: CollectionType;
  restrictedToSubCategoryId: string;
}

interface CollectionFormProps {
  initialData?: Partial<CollectionFormData>;
  mainCategories: MainCategory[];
  subCategories: SubCategory[];
  onMainCategoryChange: (mainCategoryId: string) => void;
  onSubmit: (data: CollectionFormData) => void;
  onCancel: () => void;
  isLoading: boolean;
}

const COLLECTION_TYPE_OPTIONS: CollectionType[] = [
  "single_category",
  "multi_category",
  "mixed",
];

export function CollectionForm({
  initialData,
  mainCategories,
  subCategories,
  onMainCategoryChange,
  onSubmit,
  onCancel,
  isLoading,
}: CollectionFormProps) {
  const { t } = useTranslation();

  const [name, setName] = useState(initialData?.name ?? "");
  const [description, setDescription] = useState(
    initialData?.description ?? "",
  );
  const [collectionType, setCollectionType] = useState<CollectionType>(
    initialData?.collectionType ?? "single_category",
  );
  const [mainCategoryId, setMainCategoryId] = useState("");
  const [subCategoryId, setSubCategoryId] = useState(
    initialData?.restrictedToSubCategoryId ?? "",
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setSubCategoryId("");
  }, [mainCategoryId]);

  function handleMainCategoryChange(id: string) {
    setMainCategoryId(id);
    onMainCategoryChange(id);
  }

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = t("collections.form.nameRequired");
    }

    if (collectionType === "single_category" && !subCategoryId) {
      newErrors.subCategory = t("collections.form.subCategoryRequired");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!validate()) return;

    onSubmit({
      name: name.trim(),
      description: description.trim(),
      collectionType,
      restrictedToSubCategoryId: subCategoryId,
    });
  }

  const typeOptions = COLLECTION_TYPE_OPTIONS.map((type) => ({
    value: type,
    label: t(`collections.${type === "single_category" ? "singleCategory" : type === "multi_category" ? "multiCategory" : "mixed"}`),
  }));

  const mainCategoryOptions = mainCategories.map((mc) => ({
    value: mc.id,
    label: mc.name,
  }));

  const subCategoryOptions = subCategories.map((sc) => ({
    value: sc.id,
    label: sc.name,
  }));

  const showCategorySelectors = collectionType === "single_category";

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <Input
        label={t("collections.name")}
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={errors.name}
        required
      />

      <Input
        label={t("collections.description")}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />

      <Select
        label={t("collections.type")}
        options={typeOptions}
        value={collectionType}
        onChange={(e) =>
          setCollectionType(e.target.value as CollectionType)
        }
      />

      {showCategorySelectors && (
        <>
          <Select
            label={t("collections.form.mainCategory")}
            options={mainCategoryOptions}
            value={mainCategoryId}
            onChange={(e) => handleMainCategoryChange(e.target.value)}
            placeholder={t("collections.form.selectMainCategory")}
            error={errors.mainCategory}
          />

          <Select
            label={t("collections.form.subCategory")}
            options={subCategoryOptions}
            value={subCategoryId}
            onChange={(e) => setSubCategoryId(e.target.value)}
            placeholder={t("collections.form.selectSubCategory")}
            error={errors.subCategory}
            disabled={!mainCategoryId}
          />
        </>
      )}

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
