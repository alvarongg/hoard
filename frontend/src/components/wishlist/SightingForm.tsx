import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { Sighting, SightingCreate, SightingUpdate } from "../../types/wishlist";
import { Input } from "../ui/Input";

interface SightingFormProps {
  sighting?: Sighting | null;
  onSubmit: (data: SightingCreate | SightingUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

/**
 * SightingForm - Form component for creating/editing a sighting.
 *
 * Features:
 * - Price field (required)
 * - Condition, availability, contact info
 * - Decision tracking
 * - Accessible with proper labels and error states
 */
export function SightingForm({ sighting, onSubmit, onCancel, isLoading }: SightingFormProps) {
  const { t } = useTranslation();
  const isEditing = !!sighting;

  const [formData, setFormData] = useState({
    price: sighting?.price?.toString() ?? "",
    currency: sighting?.currency ?? "USD",
    condition: sighting?.condition ?? "",
    isComplete: sighting?.isComplete?.toString() ?? "",
    isAvailable: sighting?.isAvailable?.toString() ?? "true",
    url: sighting?.url ?? "",
    locationDescription: sighting?.locationDescription ?? "",
    description: sighting?.description ?? "",
    quantityAvailable: sighting?.quantityAvailable?.toString() ?? "1",
    contacted: sighting?.contacted?.toString() ?? "false",
    contactMethod: sighting?.contactMethod ?? "",
    responseNotes: sighting?.responseNotes ?? "",
    decision: sighting?.decision ?? "",
    decisionNotes: sighting?.decisionNotes ?? "",
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

    if (!formData.price || parseFloat(formData.price) < 0) {
      newErrors.price = t("errors.sighting.priceRequired");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const data: SightingCreate | SightingUpdate = {
      price: parseFloat(formData.price),
      currency: formData.currency,
      condition: formData.condition || null,
      isComplete: formData.isComplete ? formData.isComplete === "true" : null,
      isAvailable: formData.isAvailable === "true",
      url: formData.url || null,
      locationDescription: formData.locationDescription || null,
      description: formData.description || null,
      quantityAvailable: parseInt(formData.quantityAvailable, 10) || 1,
      contacted: formData.contacted === "true",
      contactMethod: formData.contactMethod || null,
      responseNotes: formData.responseNotes || null,
      decision: (formData.decision || null) as "buy" | "pass" | "wait" | "negotiate" | null,
      decisionNotes: formData.decisionNotes || null,
    };

    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          id="price"
          label={t("wishlist.sightings.form.price")}
          type="number"
          step="0.01"
          min="0"
          value={formData.price}
          onChange={(e) => handleChange("price", e.target.value)}
          error={errors.price}
          required
        />

        <div>
          <label htmlFor="currency" className="block text-sm font-medium text-gray-700">
            {t("wishlist.sightings.form.currency")}
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
        id="condition"
        label={t("wishlist.sightings.form.condition")}
        value={formData.condition}
        onChange={(e) => handleChange("condition", e.target.value)}
      />

      <Input
        id="url"
        label={t("wishlist.sightings.form.url")}
        type="url"
        value={formData.url}
        onChange={(e) => handleChange("url", e.target.value)}
      />

      <Input
        id="locationDescription"
        label={t("wishlist.sightings.form.location")}
        value={formData.locationDescription}
        onChange={(e) => handleChange("locationDescription", e.target.value)}
      />

      <div>
        <label htmlFor="isAvailable" className="block text-sm font-medium text-gray-700">
          {t("wishlist.sightings.form.availability")}
        </label>
        <select
          id="isAvailable"
          value={formData.isAvailable}
          onChange={(e) => handleChange("isAvailable", e.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="true">{t("wishlist.sightings.available")}</option>
          <option value="false">{t("wishlist.sightings.unavailable")}</option>
        </select>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-700">{t("wishlist.sightings.form.contactSection")}</h4>

        <div className="mt-3 space-y-4">
          <div>
            <label htmlFor="contacted" className="block text-sm font-medium text-gray-700">
              {t("wishlist.sightings.form.contacted")}
            </label>
            <select
              id="contacted"
              value={formData.contacted}
              onChange={(e) => handleChange("contacted", e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="false">{t("common.no")}</option>
              <option value="true">{t("common.yes")}</option>
            </select>
          </div>

          {formData.contacted === "true" && (
            <>
              <Input
                id="contactMethod"
                label={t("wishlist.sightings.form.contactMethod")}
                value={formData.contactMethod}
                onChange={(e) => handleChange("contactMethod", e.target.value)}
              />

              <div>
                <label htmlFor="responseNotes" className="block text-sm font-medium text-gray-700">
                  {t("wishlist.sightings.form.responseNotes")}
                </label>
                <textarea
                  id="responseNotes"
                  value={formData.responseNotes}
                  onChange={(e) => handleChange("responseNotes", e.target.value)}
                  rows={2}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </>
          )}
        </div>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-700">{t("wishlist.sightings.form.decisionSection")}</h4>

        <div className="mt-3 space-y-4">
          <div>
            <label htmlFor="decision" className="block text-sm font-medium text-gray-700">
              {t("wishlist.sightings.form.decision")}
            </label>
            <select
              id="decision"
              value={formData.decision}
              onChange={(e) => handleChange("decision", e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">{t("wishlist.sightings.form.noDecision")}</option>
              <option value="buy">{t("wishlist.sightings.decision.buy")}</option>
              <option value="pass">{t("wishlist.sightings.decision.pass")}</option>
              <option value="wait">{t("wishlist.sightings.decision.wait")}</option>
              <option value="negotiate">{t("wishlist.sightings.decision.negotiate")}</option>
            </select>
          </div>

          <div>
            <label htmlFor="decisionNotes" className="block text-sm font-medium text-gray-700">
              {t("wishlist.sightings.form.decisionNotes")}
            </label>
            <textarea
              id="decisionNotes"
              value={formData.decisionNotes}
              onChange={(e) => handleChange("decisionNotes", e.target.value)}
              rows={2}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
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
