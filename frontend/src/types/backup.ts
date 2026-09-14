export type BackupFrequency = "daily" | "weekly" | "monthly";

export interface BackupInfo {
  id: string;
  filename: string;
  createdAt: string;
  sizeBytes: number;
  trigger: string;
}

export interface BackupConfig {
  frequency: BackupFrequency;
  retentionCount: number;
  nextRunAt: string | null;
  lastRunAt: string | null;
  lastRunStatus: string | null;
}

export interface BackupConfigUpdate {
  frequency?: BackupFrequency;
  retentionCount?: number;
}

export interface RestoreResult {
  restored: boolean;
  filename: string;
  message: string | null;
}
