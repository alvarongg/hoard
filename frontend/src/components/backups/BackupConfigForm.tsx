import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Select } from "../ui/Select";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type {
  BackupConfig,
  BackupConfigUpdate,
  BackupFrequency,
} from "../../types/backup";

interface BackupConfigFormProps {
  config: BackupConfig;
  onSubmit: (data: BackupConfigUpdate) => void;
  isLoading: boolean;
}

export function BackupConfigForm({
  config,
  onSubmit,
  isLoading,
}: BackupConfigFormProps) {
  const { t } = useTranslation();
  const [frequency, setFrequency] = useState<BackupFrequency>(
    config.frequency,
  );
  const [retention, setRetention] = useState(String(config.retentionCount));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          frequency,
          retentionCount: Number(retention),
        });
      }}
    >
      <div className="space-y-3">
        <Select
          label={t("backups.frequency")}
          value={frequency}
          onChange={(e) => setFrequency(e.target.value as BackupFrequency)}
          options={[
            { value: "daily", label: t("backups.frequencyDaily") },
            { value: "weekly", label: t("backups.frequencyWeekly") },
            { value: "monthly", label: t("backups.frequencyMonthly") },
          ]}
        />
        <Input
          label={t("backups.retention")}
          type="number"
          min="1"
          max="365"
          value={retention}
          onChange={(e) => setRetention(e.target.value)}
        />
        {config.nextRunAt && (
          <p className="text-sm text-gray-500">
            {t("backups.nextRun")}: {config.nextRunAt}
          </p>
        )}
        {config.lastRunStatus === "failed" && (
          <p className="text-sm text-red-600">{t("backups.lastRunFailed")}</p>
        )}
      </div>
      <Button className="mt-4" type="submit" disabled={isLoading}>
        {isLoading ? t("common.saving") : t("common.save")}
      </Button>
    </form>
  );
}
