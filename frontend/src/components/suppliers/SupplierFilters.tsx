import { useTranslation } from "react-i18next";
import type { SupplierType } from "../../types/supplier";
import { Select } from "../ui/Select";

interface SupplierFiltersProps {
  typeFilter: string;
  countryFilter: string;
  favoritesOnly: boolean;
  countries: string[];
  onTypeChange: (type: string) => void;
  onCountryChange: (country: string) => void;
  onFavoritesChange: (favoritesOnly: boolean) => void;
}

const SUPPLIER_TYPE_OPTIONS: SupplierType[] = [
  "online",
  "physical_store",
  "marketplace",
  "private_seller",
  "auction",
];

/**
 * SupplierFilters - Filter controls for the suppliers list.
 *
 * Features:
 * - Filter by supplier type
 * - Filter by country
 * - Toggle to show only favorites
 * - Accessible form controls with labels
 */
export function SupplierFilters({
  typeFilter,
  countryFilter,
  favoritesOnly,
  countries,
  onTypeChange,
  onCountryChange,
  onFavoritesChange,
}: SupplierFiltersProps) {
  const { t } = useTranslation();

  const typeOptions = [
    { value: "", label: t("suppliers.filters.all") },
    ...SUPPLIER_TYPE_OPTIONS.map((type) => ({
      value: type,
      label: t(
        `suppliers.typeOptions.${
          type === "physical_store"
            ? "store"
            : type === "private_seller"
              ? "individual"
              : type === "auction"
                ? "other"
                : type === "marketplace"
                  ? "market"
                  : type
        }`
      ),
    })),
  ];

  const countryOptions = [
    { value: "", label: t("suppliers.filters.all") },
    ...countries.map((country) => ({
      value: country,
      label: country,
    })),
  ];

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="min-w-[150px] flex-1">
        <Select
          label={t("suppliers.filters.byType")}
          options={typeOptions}
          value={typeFilter}
          onChange={(e) => onTypeChange(e.target.value)}
        />
      </div>

      <div className="min-w-[150px] flex-1">
        <Select
          label={t("suppliers.filters.byCountry")}
          options={countryOptions}
          value={countryFilter}
          onChange={(e) => onCountryChange(e.target.value)}
          disabled={countries.length === 0}
        />
      </div>

      <div className="flex items-center gap-2 pb-1">
        <input
          type="checkbox"
          id="favorites-only"
          checked={favoritesOnly}
          onChange={(e) => onFavoritesChange(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
        />
        <label
          htmlFor="favorites-only"
          className="text-sm font-medium text-gray-700"
        >
          {t("suppliers.filters.favorites")}
        </label>
      </div>
    </div>
  );
}
