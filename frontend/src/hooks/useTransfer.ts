import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { exportApi, importApi } from "../services/transferApi";
import type {
  ExportFormat,
  ImportPreview,
  BatchImportResult,
} from "../types/transfer";

type ExportTarget =
  | { kind: "collection"; id: string }
  | { kind: "catalog"; id: string; format: ExportFormat }
  | { kind: "wishlist" };

export function useExport() {
  return useMutation<void, Error, ExportTarget>({
    mutationFn: async (target) => {
      if (target.kind === "collection") {
        await exportApi.collection(target.id);
      } else if (target.kind === "catalog") {
        await exportApi.catalog(target.id, target.format);
      } else {
        await exportApi.wishlist();
      }
    },
  });
}

export type ImportStep = "upload" | "preview" | "confirm" | "report";

export function useJsonImport() {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<ImportStep>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [report, setReport] = useState<BatchImportResult | null>(null);

  const previewMutation = useMutation<ImportPreview, Error, File>({
    mutationFn: (f) => importApi.preview(f),
    onSuccess: (data) => {
      setPreview(data);
      setStep("preview");
    },
  });

  const executeMutation = useMutation<BatchImportResult, Error, File>({
    mutationFn: (f) => importApi.execute(f),
    onSuccess: (data) => {
      setReport(data);
      setStep("report");
      // Import may have created collections/items across the app.
      queryClient.invalidateQueries();
    },
  });

  const selectFile = (f: File) => {
    setFile(f);
    previewMutation.mutate(f);
  };

  const confirm = () => {
    if (file) executeMutation.mutate(file);
  };

  const cancel = () => {
    setFile(null);
    setPreview(null);
    setReport(null);
    setStep("upload");
  };

  return {
    step,
    file,
    preview,
    report,
    selectFile,
    confirm,
    cancel,
    isPreviewing: previewMutation.isPending,
    isExecuting: executeMutation.isPending,
    error: previewMutation.error ?? executeMutation.error,
  };
}
