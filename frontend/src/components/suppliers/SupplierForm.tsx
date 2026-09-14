import { useState, useId } from "react";
import { useTranslation } from "react-i18next";
import type { Supplier, SupplierType, SupplierCreate, SupplierUpdate } from "../../types/supplier";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";

interface SupplierFormProps {
  initialData?: Supplier | null;
  onSubmit: (data: SupplierCreate | SupplierUpdate) => void;
  onCancel: () => void;
  isLoading: boolean;
}

const SUPPLIER_TYPE_OPTIONS: SupplierType[] = [
  "online",
  "physical_store",
  "marketplace",
  "private_seller",
  "auction",
];

const RATING_MIN = 0;
const RATING_MAX = 5;

/**
 * SupplierForm - Form for creating and editing suppliers.
 *
 * Features:
 * - Validates name is not empty
 * - Validates rating is between 0 and 5
 * - Uses aria-invalid and aria-describedby for accessibility
 * - Supports all supplier fields
 */
export function SupplierForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}: SupplierFormProps) {
  const { t } = useTranslation();
  const formId = useId();

  const [name, setName] = useState(initialData?.name ?? "");
  const [type, setType] = useState<SupplierType | "">(initialData?.type ?? "");
  const [country, setCountry] = useState(initialData?.country ?? "");
  const [stateProvince, setStateProvince] = useState(
    initialData?.stateProvince ?? "",
  );
  const [city, setCity] = useState(initialData?.city ?? "");
  const [address, setAddress] = useState(initialData?.address ?? "");
  const [postalCode, setPostalCode] = useState(initialData?.postalCode ?? "");
  const [website, setWebsite] = useState(initialData?.website ?? "");
  const [email, setEmail] = useState(initialData?.email ?? "");
  const [phone, setPhone] = useState(initialData?.phone ?? "");
  const [marketplaceUrl, setMarketplaceUrl] = useState(
    initialData?.marketplaceUrl ?? "",
  );
  const [rating, setRating] = useState(
    initialData?.rating !== null && initialData?.rating !== undefined
      ? String(initialData.rating)
      : "",
  );
  const [notes, setNotes] = useState(initialData?.notes ?? "");
  const [isActive, setIsActive] = useState(initialData?.isActive ?? true);

  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    // Name validation: not empty
    if (!name.trim()) {
      newErrors.name = t("errors.supplier.nameRequired");
    }

    // Rating validation: must be between 0 and 5 if provided
    if (rating.trim()) {
      const ratingNum = parseFloat(rating);
      if (isNaN(ratingNum) || ratingNum < RATING_MIN || ratingNum > RATING_MAX) {
        newErrors.rating = t("errors.supplier.ratingRange");
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!validate()) return;

    const ratingValue = rating.trim() ? parseFloat(rating) : null;

    onSubmit({
      name: name.trim(),
      type: type || null,
      country: country.trim() || null,
      stateProvince: stateProvince.trim() || null,
      city: city.trim() || null,
      address: address.trim() || null,
      postalCode: postalCode.trim() || null,
      website: website.trim() || null,
      email: email.trim() || null,
      phone: phone.trim() || null,
      marketplaceUrl: marketplaceUrl.trim() || null,
      rating: ratingValue,
      notes: notes.trim() || null,
      isActive,
    });
  }

  const typeOptions = [
    { value: "", label: t("suppliers.filters.all") },
    ...SUPPLIER_TYPE_OPTIONS.map((typeOption) => ({
      value: typeOption,
      label: t(
        `suppliers.typeOptions.${
          typeOption === "physical_store"
            ? "store"
            : typeOption === "private_seller"
              ? "individual"
              : typeOption === "auction"
                ? "other"
                : typeOption === "marketplace"
                  ? "market"
                  : typeOption
        }`
      ),
    })),
  ];

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <Input
        label={t("suppliers.name")}
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={errors.name}
        required
      />

      <Select
        label={t("suppliers.type")}
        options={typeOptions}
        value={type}
        onChange={(e) => setType(e.target.value as SupplierType | "")}
      />

      <div className="grid grid-cols-2 gap-4">
        <Input
          label={t("suppliers.country")}
          value={country}
          onChange={(e) => setCountry(e.target.value)}
        />
        <Input
          label={t("suppliers.city")}
          value={city}
          onChange={(e) => setCity(e.target.value)}
        />
      </div>

      <Input
        label={t("suppliers.stateProvince")}
        value={stateProvince}
        onChange={(e) => setStateProvince(e.target.value)}
      />

      <Input
        label={t("suppliers.address")}
        value={address}
        onChange={(e) => setAddress(e.target.value)}
      />

      <Input
        label={t("suppliers.postalCode")}
        value={postalCode}
        onChange={(e) => setPostalCode(e.target.value)}
      />

      <Input
        label={t("suppliers.rating")}
        type="number"
        value={rating}
        onChange={(e) => setRating(e.target.value)}
        error={errors.rating}
        min={RATING_MIN}
        max={RATING_MAX}
        step="0.01"
        placeholder="0.00 - 5.00"
      />

      <Input
        label={t("suppliers.website")}
        type="url"
        value={website}
        onChange={(e) => setWebsite(e.target.value)}
        placeholder="https://example.com"
      />

      <Input
        label={t("suppliers.email")}
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <Input
        label={t("suppliers.phone")}
        type="tel"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
      />

      <Input
        label={t("suppliers.marketplaceUrl")}
        type="url"
        value={marketplaceUrl}
        onChange={(e) => setMarketplaceUrl(e.target.value)}
        placeholder="https://ebay.com/usr/sellername"
      />

      <div className="flex flex-col gap-1">
        <label htmlFor={`${formId}-notes`} className="text-sm font-medium text-gray-700">
          {t("suppliers.notes")}
        </label>
        <textarea
          id={`${formId}-notes`}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id={`${formId}-active`}
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
        />
        <label htmlFor={`${formId}-active`} className="text-sm font-medium text-gray-700">
          {t("suppliers.active")}
        </label>
      </div>

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
