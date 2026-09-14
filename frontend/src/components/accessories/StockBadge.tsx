import { useTranslation } from "react-i18next";
import { Badge } from "../ui/Badge";

interface StockBadgeProps {
  quantityAvailable: number;
  isLowStock: boolean;
}

/** StockBadge - conveys stock level with text + tone (never color alone). */
export function StockBadge({ quantityAvailable, isLowStock }: StockBadgeProps) {
  const { t } = useTranslation();
  const label = isLowStock
    ? t("accessories.lowStock", { count: quantityAvailable })
    : t("accessories.inStock", { count: quantityAvailable });
  return (
    <Badge
      label={label}
      tone={isLowStock ? "warning" : "success"}
      icon={<span aria-hidden="true">{isLowStock ? "⚠" : "✓"}</span>}
    />
  );
}
