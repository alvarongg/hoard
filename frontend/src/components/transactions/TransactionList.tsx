import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import type { Transaction } from "../../types/transaction";

interface TransactionListProps {
  transactions: Transaction[];
  onDelete?: (id: string) => void;
}

/** TransactionList - accessible table of item transactions (newest first). */
export function TransactionList({
  transactions,
  onDelete,
}: TransactionListProps) {
  const { t } = useTranslation();

  if (transactions.length === 0) {
    return <EmptyState title={t("transactions.empty")} />;
  }

  const columns: TableColumn<Transaction>[] = [
    {
      key: "transactionDate",
      header: t("transactions.date"),
      accessor: (row) => row.transactionDate,
      sortable: true,
    },
    {
      key: "transactionType",
      header: t("transactions.type.label"),
      accessor: (row) => t(`transactions.type.${row.transactionType}`),
    },
    {
      key: "totalAmount",
      header: t("transactions.totalAmount"),
      accessor: (row) => `${row.totalAmount} ${row.currency}`,
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
          aria-label={t("transactions.deleteEntry", {
            date: row.transactionDate,
          })}
        >
          {t("common.delete")}
        </Button>
      ),
    });
  }

  return (
    <Table
      caption={t("transactions.title")}
      columns={columns}
      rows={transactions}
      getRowKey={(row) => row.id}
    />
  );
}
