import { useTranslation } from "react-i18next";
import { Table, type TableColumn } from "../ui/Table";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import type { BackupInfo } from "../../types/backup";

interface BackupListProps {
  backups: BackupInfo[];
  onDownload: (id: string) => void;
  onRestore: (backup: BackupInfo) => void;
  onDelete: (id: string) => void;
}

export function BackupList({
  backups,
  onDownload,
  onRestore,
  onDelete,
}: BackupListProps) {
  const { t } = useTranslation();

  if (backups.length === 0) {
    return <EmptyState title={t("backups.empty")} />;
  }

  const columns: TableColumn<BackupInfo>[] = [
    {
      key: "createdAt",
      header: t("backups.createdAt"),
      accessor: (r) => r.createdAt,
      sortable: true,
    },
    {
      key: "sizeBytes",
      header: t("backups.size"),
      accessor: (r) => `${(r.sizeBytes / 1024).toFixed(1)} KB`,
    },
    {
      key: "actions",
      header: t("common.actions"),
      accessor: (r) => (
        <span className="flex gap-2">
          <Button variant="secondary" onClick={() => onDownload(r.id)}>
            {t("backups.download")}
          </Button>
          <Button variant="secondary" onClick={() => onRestore(r)}>
            {t("backups.restore")}
          </Button>
          <Button variant="danger" onClick={() => onDelete(r.id)}>
            {t("common.delete")}
          </Button>
        </span>
      ),
    },
  ];

  return (
    <Table
      caption={t("backups.title")}
      columns={columns}
      rows={backups}
      getRowKey={(r) => r.id}
    />
  );
}
