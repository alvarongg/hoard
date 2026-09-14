import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Button } from "../components/ui/Button";
import { BackupList } from "../components/backups/BackupList";
import { BackupConfigForm } from "../components/backups/BackupConfigForm";
import { RestoreConfirmDialog } from "../components/backups/RestoreConfirmDialog";
import { useBackups, useBackupConfig } from "../hooks/useBackups";
import { backupsApi } from "../services/backupsApi";
import type { BackupInfo } from "../types/backup";

export function BackupsPage() {
  const { t } = useTranslation();
  const backups = useBackups();
  const config = useBackupConfig();
  const [restoring, setRestoring] = useState<BackupInfo | null>(null);

  const createError = backups.create.error;
  const toolUnavailable =
    createError?.message?.toLowerCase().includes("pg_dump") ||
    createError?.message?.includes("503");

  return (
    <main>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t("backups.title")}
        </h1>
        <Button
          onClick={() => backups.create.mutate()}
          disabled={backups.create.isPending}
        >
          {t("backups.create")}
        </Button>
      </div>

      {toolUnavailable && (
        <div className="mt-3">
          <ErrorMessage message={t("backups.toolUnavailable")} />
        </div>
      )}

      <section aria-label={t("backups.title")} className="mt-6">
        {backups.isLoading && <LoadingSpinner />}
        {backups.isError && (
          <ErrorMessage
            message={t("errors.loadFailed")}
            onRetry={() => backups.refetch()}
          />
        )}
        {!backups.isLoading && !backups.isError && (
          <BackupList
            backups={backups.data ?? []}
            onDownload={(id) => void backupsApi.download(id)}
            onRestore={(b) => setRestoring(b)}
            onDelete={(id) => backups.remove.mutate(id)}
          />
        )}
      </section>

      <section aria-label={t("backups.config")} className="mt-8 max-w-md">
        <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
          {t("backups.config")}
        </h2>
        {config.data && (
          <BackupConfigForm
            config={config.data}
            isLoading={config.update.isPending}
            onSubmit={(data) => config.update.mutate(data)}
          />
        )}
      </section>

      <RestoreConfirmDialog
        isOpen={restoring !== null}
        filename={restoring?.filename ?? ""}
        isLoading={backups.restore.isPending}
        onClose={() => setRestoring(null)}
        onConfirm={() => {
          if (restoring) {
            backups.restore.mutate(restoring.id, {
              onSuccess: () => setRestoring(null),
            });
          }
        }}
      />
    </main>
  );
}
