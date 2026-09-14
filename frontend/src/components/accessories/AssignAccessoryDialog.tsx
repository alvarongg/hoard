import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Modal } from "../ui/Modal";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";
import type { Accessory } from "../../types/accessory";

interface AssignAccessoryDialogProps {
  isOpen: boolean;
  accessories: Accessory[];
  onClose: () => void;
  onAssign: (accessoryId: string, quantityUsed: number) => void;
  isLoading: boolean;
}

export function AssignAccessoryDialog({
  isOpen,
  accessories,
  onClose,
  onAssign,
  isLoading,
}: AssignAccessoryDialogProps) {
  const { t } = useTranslation();
  const [accessoryId, setAccessoryId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [error, setError] = useState("");

  const selected = accessories.find((a) => a.id === accessoryId);

  function handleAssign() {
    const qty = Number(quantity);
    if (!accessoryId) {
      setError(t("errors.accessory.selectRequired"));
      return;
    }
    if (selected && qty > selected.quantityAvailable) {
      setError(t("errors.accessory.insufficientStock"));
      return;
    }
    setError("");
    onAssign(accessoryId, qty);
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t("accessories.assign")}>
      <div className="space-y-3">
        <Select
          label={t("accessories.title")}
          value={accessoryId}
          onChange={(e) => setAccessoryId(e.target.value)}
          placeholder="—"
          options={accessories.map((a) => ({
            value: a.id,
            label: `${a.name} (${a.quantityAvailable})`,
          }))}
        />
        <Input
          label={t("accessories.quantityUsed")}
          type="number"
          min="1"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          error={error}
        />
        <div className="flex gap-2">
          <Button onClick={handleAssign} disabled={isLoading}>
            {t("accessories.assign")}
          </Button>
          <Button variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
