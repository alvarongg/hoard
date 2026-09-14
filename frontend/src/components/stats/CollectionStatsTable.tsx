import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import { EmptyState } from "../ui/EmptyState";
import type { CollectionStatsEntry } from "../../types/stats";

interface CollectionStatsTableProps {
  entries: CollectionStatsEntry[];
}

export function CollectionStatsTable({ entries }: CollectionStatsTableProps) {
  const { t } = useTranslation();

  if (entries.length === 0) {
    return <EmptyState title={t("stats.empty")} />;
  }

  const columns: TableColumn<CollectionStatsEntry>[] = [
    {
      key: "collectionName",
      header: t("stats.byCollection"),
      accessor: (r) => r.collectionName,
    },
    {
      key: "totalItems",
      header: t("stats.totalItems"),
      accessor: (r) => String(r.totalItems),
    },
    {
      key: "totalInvested",
      header: t("stats.totalInvested"),
      accessor: (r) => r.totalInvested,
    },
    {
      key: "currentValue",
      header: t("stats.totalValue"),
      accessor: (r) => r.currentValue,
    },
    {
      key: "roiPercentage",
      header: t("stats.roi"),
      accessor: (r) =>
        r.roiPercentage === null
          ? t("stats.roiUnavailable")
          : `${r.roiPercentage}%`,
    },
  ];

  return (
    <Table
      caption={t("stats.byCollection")}
      columns={columns}
      rows={entries}
      getRowKey={(r) => r.collectionId}
    />
  );
}
