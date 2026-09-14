import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import { EmptyState } from "../ui/EmptyState";
import type { ImportEntityChange } from "../../types/transfer";

interface ImportPreviewTableProps {
  changes: ImportEntityChange[];
}

export function ImportPreviewTable({ changes }: ImportPreviewTableProps) {
  const { t } = useTranslation();

  if (changes.length === 0) {
    return <EmptyState title={t("import.empty")} />;
  }

  const columns: TableColumn<ImportEntityChange>[] = [
    {
      key: "entityType",
      header: t("import.entity"),
      accessor: (r) => r.entityType,
    },
    {
      key: "identifier",
      header: "ID",
      accessor: (r) => r.identifier,
    },
    {
      key: "action",
      header: t("import.action"),
      accessor: (r) => t(`import.actions.${r.action}`),
    },
  ];

  return (
    <Table
      caption={t("import.preview")}
      columns={columns}
      rows={changes}
      getRowKey={(r, i) => `${r.entityType}-${r.identifier}-${i}`}
    />
  );
}
