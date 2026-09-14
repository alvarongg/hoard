import { useTranslation } from "react-i18next";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { StockBadge } from "./StockBadge";
import type { Accessory } from "../../types/accessory";

interface AccessoryCardProps {
  accessory: Accessory;
  onEdit?: (accessory: Accessory) => void;
  onDelete?: (id: string) => void;
}

export function AccessoryCard({
  accessory,
  onEdit,
  onDelete,
}: AccessoryCardProps) {
  const { t } = useTranslation();

  return (
    <Card title={accessory.name}>
      <div className="mb-2">
        <StockBadge
          quantityAvailable={accessory.quantityAvailable}
          isLowStock={accessory.isLowStock}
        />
      </div>
      <dl className="text-sm text-gray-600 dark:text-gray-300">
        <div className="flex justify-between">
          <dt>{t("accessories.quantityTotal")}</dt>
          <dd>{accessory.quantityTotal}</dd>
        </div>
        <div className="flex justify-between">
          <dt>{t("accessories.quantityInUse")}</dt>
          <dd>{accessory.quantityInUse}</dd>
        </div>
        <div className="flex justify-between">
          <dt>{t("accessories.quantityAvailable")}</dt>
          <dd>{accessory.quantityAvailable}</dd>
        </div>
      </dl>
      <div className="mt-3 flex gap-2">
        {onEdit && (
          <Button variant="secondary" onClick={() => onEdit(accessory)}>
            {t("common.edit")}
          </Button>
        )}
        {onDelete && (
          <Button variant="danger" onClick={() => onDelete(accessory.id)}>
            {t("common.delete")}
          </Button>
        )}
      </div>
    </Card>
  );
}
