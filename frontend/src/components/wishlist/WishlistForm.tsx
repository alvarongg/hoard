import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { WishlistItem, WishlistItemCreate, WishlistItemUpdate, Priority, Urgency } from "../../types/wishlist";
import { Input } from "../ui/Input";

interface WishlistFormProps {
  item?: WishlistItem | null;
  onSubmit: (data: WishlistItemCreate | WishlistItemUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

/**
 * WishlistForm - Form component for creating/editing a wishlist item.
 *
 * Features:
 * - Priority and urgency selection
 * - Budget and condition settings
 * - Completeness requirements
 * - Accessible with proper labels and error states
 */
export function WishlistForm({ item, onSubmit, onCancel, isLoading }: WishlistFormProps) {
  const { t } = useTranslation();
  const isEditing = !!item;

  const [formData, setFormData] = useState({
    desiredCondition: item?.desiredCondition ?? "",
    desiredConditionMin: item?.desiredConditionMin ?? "",
    mustBeComplete: item?.mustBeComplete?.toString() ?? "true",
    desiredCompletenessDescription: item?.desiredCompletenessDescription ?? "",
    maxPrice: item?.maxPrice?.toString() ?? "",
    currency: item?.currency ?? "USD",
    specificVariantRequired: item?.specificVariantRequired?.toString() ?? "false",
    variantDescription: item?.variantDescription ?? "",
    priority: item?.priority?.toString() ?? "3",
    urgency: item?.urgency ?? "medium",
    notes: item?.notes ?? "",
    searchNotes: item?.searchNotes ?? "",
    isActive: item?.isActive?.toString() ?? "true",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    const priorityNum = parseInt(formData.priority, 10);
    if (priorityNum < 1 || priorityNum > 5) {
      newErrors.priority = t("errors.wishlist.priorityRange");
    }

    const validUrgencies: Urgency[] = ["low", "medium", "high", "critical"];
    if (!validUrgencies.includes(formData.urgency as Urgency)) {
      newErrors.urgency = t("errors.wishlist.invalidUrgency");
    }

    if (formData.maxPrice && parseFloat(formData.maxPrice) < 0) {
      newErrors.maxPrice = t("errors.wishlist.maxPriceNegative");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const data: WishlistItemUpdate = {
      desiredCondition: formData.desiredCondition || null,
      desiredConditionMin: formData.desiredConditionMin || null,
      mustBeComplete: formData.mustBeComplete === "true",
      desiredCompletenessDescription: formData.desiredCompletenessDescription || null,
      maxPrice: formData.maxPrice ? parseFloat(formData.maxPrice) : null,
      currency: formData.currency,
      specificVariantRequired: formData.specificVariantRequired === "true",
      variantDescription: formData.variantDescription || null,
      priority: parseInt(formData.priority, 10) as Priority,
      urgency: formData.urgency as Urgency,
      notes: formData.notes || null,
      searchNotes: formData.searchNotes || null,
      isActive: formData.isActive === "true",
    };

    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
            {t("wishlist.form.priority")}
          </label>
          <select
            id="priority"
            value={formData.priority}
            onChange={(e) => handleChange("priority", e.target.value)}
            aria-invalid={!!errors.priority}
            aria-describedby={errors.priority ? "priority-error" : undefined}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="1">{t("wishlist.priority.critical")} (1)</option>
            <option value="2">{t("wishlist.priority.high")} (2)</option>
            <option value="3">{t("wishlist.priority.medium")} (3)</option>
            <option value="4">{t("wishlist.priority.low")} (4)</option>
            <option value="5">{t("wishlist.priority.lowest")} (5)</option>
          </select>
          {errors.priority && (
            <p id="priority-error" className="mt-1 text-sm text-red-600">
              {errors.priority}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="urgency" className="block text-sm font-medium text-gray-700">
            {t("wishlist.form.urgency")}
          </label>
          <select
            id="urgency"
            value={formData.urgency}
            onChange={(e) => handleChange("urgency", e.target.value)}
            aria-invalid={!!errors.urgency}
            aria-describedby={errors.urgency ? "urgency-error" : undefined}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="low">{t("wishlist.urgency.low")}</option>
            <option value="medium">{t("wishlist.urgency.medium")}</option>
            <option value="high">{t("wishlist.urgency.high")}</option>
            <option value="critical">{t("wishlist.urgency.critical")}</option>
          </select>
          {errors.urgency && (
            <p id="urgency-error" className="mt-1 text-sm text-red-600">
              {errors.urgency}
            </p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          id="maxPrice"
          label={t("wishlist.form.maxPrice")}
          type="number"
          step="0.01"
          min="0"
          value={formData.maxPrice}
          onChange={(e) => handleChange("maxPrice", e.target.value)}
          error={errors.maxPrice}
        />

        <div>
          <label htmlFor="currency" className="block text-sm font-medium text-gray-700">
            {t("wishlist.form.currency")}
          </label>
          <select
            id="currency"
            value={formData.currency}
            onChange={(e) => handleChange("currency", e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
          </select>
        </div>
      </div>

      <Input
        id="desiredCondition"
        label={t("wishlist.form.desiredCondition")}
        value={formData.desiredCondition}
        onChange={(e) => handleChange("desiredCondition", e.target.value)}
      />

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="mustBeComplete"
          checked={formData.mustBeComplete === "true"}
          onChange={(e) => handleChange("mustBeComplete", e.target.checked.toString())}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label htmlFor="mustBeComplete" className="text-sm font-medium text-gray-700">
          {t("wishlist.form.mustBeComplete")}
        </label>
      </div>

      {formData.mustBeComplete === "true" && (
        <div>
          <label htmlFor="desiredCompletenessDescription" className="block text-sm font-medium text-gray-700">
            {t("wishlist.form.completenessDescription")}
          </label>
          <textarea
            id="desiredCompletenessDescription"
            value={formData.desiredCompletenessDescription}
            onChange={(e) => handleChange("desiredCompletenessDescription", e.target.value)}
            rows={2}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="specificVariantRequired"
          checked={formData.specificVariantRequired === "true"}
          onChange={(e) => handleChange("specificVariantRequired", e.target.checked.toString())}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label htmlFor="specificVariantRequired" className="text-sm font-medium text-gray-700">
          {t("wishlist.form.specificVariantRequired")}
        </label>
      </div>

      {formData.specificVariantRequired === "true" && (
        <Input
          id="variantDescription"
          label={t("wishlist.form.variantDescription")}
          value={formData.variantDescription}
          onChange={(e) => handleChange("variantDescription", e.target.value)}
        />
      )}

      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
          {t("wishlist.form.notes")}
        </label>
        <textarea
          id="notes"
          value={formData.notes}
          onChange={(e) => handleChange("notes", e.target.value)}
          rows={3}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="searchNotes" className="block text-sm font-medium text-gray-700">
          {t("wishlist.form.searchNotes")}
        </label>
        <textarea
          id="searchNotes"
          value={formData.searchNotes}
          onChange={(e) => handleChange("searchNotes", e.target.value)}
          rows={2}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="isActive" className="block text-sm font-medium text-gray-700">
          {t("wishlist.form.status")}
        </label>
        <select
          id="isActive"
          value={formData.isActive}
          onChange={(e) => handleChange("isActive", e.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="true">{t("wishlist.form.active")}</option>
          <option value="false">{t("wishlist.form.inactive")}</option>
        </select>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {t("common.cancel")}
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isLoading ? t("common.saving") : (isEditing ? t("common.save") : t("common.create"))}
        </button>
      </div>
    </form>
  );
}
