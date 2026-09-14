import { API_BASE_URL, fetchApi, toSnakeCase } from "./api";
import type {
  BackupInfo,
  BackupConfig,
  BackupConfigUpdate,
  RestoreResult,
} from "../types/backup";

export const backupsApi = {
  list: (): Promise<BackupInfo[]> => fetchApi<BackupInfo[]>("/backups"),

  create: (): Promise<BackupInfo> =>
    fetchApi<BackupInfo>("/backups", { method: "POST" }),

  download: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/backups/${id}/download`);
    if (!response.ok) throw new Error(`Download failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = id;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  restore: (id: string): Promise<RestoreResult> =>
    fetchApi<RestoreResult>(`/backups/${id}/restore`, { method: "POST" }),

  remove: (id: string): Promise<void> =>
    fetchApi<void>(`/backups/${id}`, { method: "DELETE" }),

  getConfig: (): Promise<BackupConfig> =>
    fetchApi<BackupConfig>("/backups/config"),

  updateConfig: (data: BackupConfigUpdate): Promise<BackupConfig> =>
    fetchApi<BackupConfig>("/backups/config", {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),
};
