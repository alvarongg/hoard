import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useCollections } from "../../hooks/useCollections";
import { useSuppliers } from "../../hooks/useSuppliers";
import type { CollectionItemCreate, ItemCondition } from "../../types/item";
import type { MaintenanceCreate } from "../../types/collectorWorkflow";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { SupplierQuickAdd } from "./SupplierQuickAdd";

const CONDITIONS: ItemCondition[] = [
  "mint",
  "near_mint",
  "excellent",
  "good",
  "fair",
  "poor",
];

export interface AddToCollectionResult {
  collectionId: string;
  data: CollectionItemCreate;
  maintenance: MaintenanceCreate | null;
  removeFromWishlist: boolean;
}

interface AddToCollectionFormProps {
  catalogItemId: string;
  /** Pre-set collection (wishlist flow); when set the selector is hidden. */
  fixedCollectionId?: string;
  /** Show the "remove from wishlist" toggle (wishlist "ya lo conseguí"). */
  showWishlistToggle?: boolean;
  onSubmit: (result: AddToCollectionResult) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function AddToCollectionForm({
  catalogItemId,
  fixedCollectionId,
  showWishlistToggle = false,
  onSubmit,
  onCancel,
  isLoading = false,
}: AddToCollectionFormProps) {
  const { t } = useTranslation();
  const { data: collections = [] } = useCollections();
  const { data: suppliers = [] } = useSuppliers();

  const [collectionId, setCollectionId] = useState(fixedCollectionId ?? "");
  const [condition, setCondition] = useState<ItemCondition>("good");
  const [isAuthentic, setIsAuthentic] = useState(true);
  const [countryOfOrigin, setCountryOfOrigin] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [purchaseCurrency, setPurchaseCurrency] = useState("USD");
  const [supplierId, setSupplierId] = useState("");
  const [storageLocation, setStorageLocation] = useState("");
  const [conditionNotes, setConditionNotes] = useState("");
  const [showSupplierQuickAdd, setShowSupplierQuickAdd] = useState(false);
  const [needsMaintenance, setNeedsMaintenance] = useState(false);
  const [maintenanceType, setMaintenanceType] = useState("battery");
  const [maintenanceDue, setMaintenanceDue] = useState("");
  const [removeFromWishlist, setRemoveFromWishlist] = useState(true);

  const canSubmit = Boolean(collectionId) && !isLoading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    const data: CollectionItemCreate = {
      catalogItemId,
      condition,
      isAuthentic,
    };
    if (countryOfOrigin.trim())
      data.countryOfOrigin = countryOfOrigin.trim().toUpperCase();
    if (purchasePrice.trim()) data.purchasePrice = Number(purchasePrice);
    data.purchaseCurrency = purchaseCurrency;
    if (supplierId) data.supplierId = supplierId;
    if (storageLocation.trim()) data.storageLocation = storageLocation.trim();
    if (conditionNotes.trim()) data.conditionNotes = conditionNotes.trim();

    const maintenance: MaintenanceCreate | null =
      needsMaintenance && maintenanceDue
        ? { maintenanceType, dueDate: maintenanceDue }
        : null;

    onSubmit({ collectionId, data, maintenance, removeFromWishlist });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      {!fixedCollectionId && (
        <Select
          label={t("collector.addToCollection.collection")}
          value={collectionId}
          onChange={(e) => setCollectionId(e.target.value)}
          options={[
            { value: "", label: t("collector.addToCollection.chooseCollection") },
            ...collections.map((c) => ({ value: c.id, label: c.name })),
          ]}
          required
        />
      )}

      <Select
        label={t("collector.addToCollection.condition")}
        value={condition}
        onChange={(e) => setCondition(e.target.value as ItemCondition)}
        options={CONDITIONS.map((c) => ({
          value: c,
          label: t(`items.${c === "near_mint" ? "nearMint" : c}`),
        }))}
      />

      <fieldset className="flex items-center gap-4">
        <legend className="text-sm font-medium">
          {t("collector.addToCollection.authenticity")}
        </legend>
        <label className="flex items-center gap-1 text-sm">
          <input
            type="radio"
            name="authenticity"
            checked={isAuthentic}
            onChange={() => setIsAuthentic(true)}
          />
          {t("collector.addToCollection.original")}
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input
            type="radio"
            name="authenticity"
            checked={!isAuthentic}
            onChange={() => setIsAuthentic(false)}
          />
          {t("collector.addToCollection.bootleg")}
        </label>
      </fieldset>

      <Input
        label={t("collector.addToCollection.country")}
        value={countryOfOrigin}
        maxLength={2}
        placeholder="JP"
        onChange={(e) => setCountryOfOrigin(e.target.value.toUpperCase())}
      />

      <div className="flex gap-2">
        <Input
          label={t("collector.addToCollection.price")}
          type="number"
          min="0"
          step="0.01"
          value={purchasePrice}
          onChange={(e) => setPurchasePrice(e.target.value)}
        />
        <Input
          label={t("collector.addToCollection.currency")}
          value={purchaseCurrency}
          maxLength={3}
          onChange={(e) => setPurchaseCurrency(e.target.value.toUpperCase())}
        />
      </div>

      {showSupplierQuickAdd ? (
        <SupplierQuickAdd
          onCreated={(id) => {
            setSupplierId(id);
            setShowSupplierQuickAdd(false);
          }}
          onCancel={() => setShowSupplierQuickAdd(false)}
        />
      ) : (
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Select
              label={t("collector.addToCollection.supplier")}
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
              options={[
                { value: "", label: t("collector.addToCollection.noSupplier") },
                ...suppliers.map((s) => ({ value: s.id, label: s.name })),
              ]}
            />
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setShowSupplierQuickAdd(true)}
          >
            {t("collector.addToCollection.newSupplier")}
          </Button>
        </div>
      )}

      <Input
        label={t("collector.addToCollection.storageLocation")}
        value={storageLocation}
        onChange={(e) => setStorageLocation(e.target.value)}
      />

      <Input
        label={t("collector.addToCollection.conditionNotes")}
        value={conditionNotes}
        onChange={(e) => setConditionNotes(e.target.value)}
      />

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={needsMaintenance}
          onChange={(e) => setNeedsMaintenance(e.target.checked)}
        />
        {t("collector.addToCollection.needsMaintenance")}
      </label>
      {needsMaintenance && (
        <div className="flex gap-2 pl-6">
          <Input
            label={t("collector.addToCollection.maintenanceType")}
            value={maintenanceType}
            onChange={(e) => setMaintenanceType(e.target.value)}
          />
          <Input
            label={t("collector.addToCollection.maintenanceDue")}
            type="date"
            value={maintenanceDue}
            onChange={(e) => setMaintenanceDue(e.target.value)}
          />
        </div>
      )}

      {showWishlistToggle && (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={removeFromWishlist}
            onChange={(e) => setRemoveFromWishlist(e.target.checked)}
          />
          {t("collector.addToCollection.removeFromWishlist")}
        </label>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={!canSubmit}>
          {t("collector.addToCollection.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </form>
  );
}
