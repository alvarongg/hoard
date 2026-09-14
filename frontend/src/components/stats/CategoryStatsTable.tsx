import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import { EmptyState } from "../ui/EmptyState";
import type { CategoryStatsEntry } from "../../types/stats";

interface CategoryStatsTableProps {
  entries: CategoryStatsEntry[];
}

export function CategoryStatsTable({ entries }: CategoryStatsTableProps) {
  const { t } = useTranslation();

  if (entries.length === 0) {
    return <EmptyState title={t("stats.empty")} />;
  }

  const columns: TableColumn<CategoryStatsEntry>[] = [
    {
      key: "subCategoryName",
      header: t("stats.byCategory"),
      accessor: (r) => r.subCategoryName,
    },
    {
      key: "itemCount",
      header: t("stats.totalItems"),
      accessor: (r) => String(r.itemCount),
    },
    {
      key: "currentValue",
      header: t("stats.totalValue"),
      accessor: (r) => r.currentValue,
    },
  ];

  return (
    <Table
      caption={t("stats.byCategory")}
      columns={columns}
      rows={entries}
      getRowKey={(r) => r.subCategoryId ?? r.subCategoryName}
    />
  );
}
