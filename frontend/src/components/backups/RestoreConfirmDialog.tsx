import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Modal } from "../ui/Modal";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

interface RestoreConfirmDialogProps {
  isOpen: boolean;
  filename: string;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

/**
 * RestoreConfirmDialog - destructive, irreversible action.
 * Requires typing the confirmation word to enable the restore button.
 */
export function RestoreConfirmDialog({
  isOpen,
  filename,
  onClose,
  onConfirm,
  isLoading,
}: RestoreConfirmDialogProps) {
  const { t } = useTranslation();
  const [typed, setTyped] = useState("");
  const confirmWord = t("backups.restoreConfirmWord");
  const enabled = typed.trim() === confirmWord;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t("backups.restore")}>
      <p className="text-sm text-red-700 dark:text-red-400">
        {t("backups.restoreWarning", { filename })}
      </p>
      <div className="mt-3">
        <Input
          label={t("backups.restoreConfirmPrompt", { word: confirmWord })}
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
        />
      </div>
      <div className="mt-4 flex gap-2">
        <Button variant="danger" onClick={onConfirm} disabled={!enabled || isLoading}>
          {t("backups.restore")}
        </Button>
        <Button variant="secondary" onClick={onClose}>
          {t("common.cancel")}
        </Button>
      </div>
    </Modal>
  );
}
