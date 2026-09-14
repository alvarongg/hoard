import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { backupsApi } from "../services/backupsApi";
import type {
  BackupInfo,
  BackupConfig,
  BackupConfigUpdate,
  RestoreResult,
} from "../types/backup";

const BACKUPS_KEY = ["backups"] as const;

export function useBackups() {
  const queryClient = useQueryClient();

  const query = useQuery<BackupInfo[], Error>({
    queryKey: BACKUPS_KEY,
    queryFn: () => backupsApi.list(),
  });

  const create = useMutation<BackupInfo, Error, void>({
    mutationFn: () => backupsApi.create(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: BACKUPS_KEY }),
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (id) => backupsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: BACKUPS_KEY }),
  });

  const restore = useMutation<RestoreResult, Error, string>({
    mutationFn: (id) => backupsApi.restore(id),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  return { ...query, create, remove, restore };
}

export function useBackupConfig() {
  const queryClient = useQueryClient();

  const query = useQuery<BackupConfig, Error>({
    queryKey: [...BACKUPS_KEY, "config"],
    queryFn: () => backupsApi.getConfig(),
  });

  const update = useMutation<BackupConfig, Error, BackupConfigUpdate>({
    mutationFn: (data) => backupsApi.updateConfig(data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: [...BACKUPS_KEY, "config"] }),
  });

  return { ...query, update };
}
