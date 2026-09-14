import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import type { PriceHistoryEntry } from "../../types/priceHistory";

interface PriceHistoryTableProps {
  entries: PriceHistoryEntry[];
  onDelete?: (id: string) => void;
}

/**
 * PriceHistoryTable - accessible table of catalog price records.
 * Rows arrive newest-first from the API (ordered by price_date desc).
 */
export function PriceHistoryTable({ entries, onDelete }: PriceHistoryTableProps) {
  const { t } = useTranslation();

  if (entries.length === 0) {
    return <EmptyState title={t("priceHistory.empty")} />;
  }

  const columns: TableColumn<PriceHistoryEntry>[] = [
    {
      key: "priceDate",
      header: t("priceHistory.priceDate"),
      accessor: (row) => row.priceDate,
      sortable: true,
    },
    {
      key: "condition",
      header: t("priceHistory.condition"),
      accessor: (row) => row.condition,
    },
    {
      key: "isComplete",
      header: t("priceHistory.isComplete"),
      accessor: (row) =>
        row.isComplete ? t("common.yes") : t("common.no"),
    },
    {
      key: "price",
      header: t("priceHistory.price"),
      accessor: (row) => `${row.price} ${row.currency}`,
    },
    {
      key: "source",
      header: t("priceHistory.source"),
      accessor: (row) => row.source ?? "—",
    },
  ];

  if (onDelete) {
    columns.push({
      key: "actions",
      header: t("common.actions"),
      accessor: (row) => (
        <Button
          variant="danger"
          onClick={() => onDelete(row.id)}
          aria-label={t("priceHistory.deleteEntry", { date: row.priceDate })}
        >
          {t("common.delete")}
        </Button>
      ),
    });
  }

  return (
    <Table
      caption={t("priceHistory.title")}
      columns={columns}
      rows={entries}
      getRowKey={(row) => row.id}
    />
  );
}
