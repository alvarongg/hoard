import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const { t } = useTranslation();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  // Keep the latest onClose in a ref so the open/close effect does NOT
  // depend on its identity. Otherwise a parent re-render (e.g. changing a
  // category select, which refetches sub-categories) would give a new
  // onClose, tear down the effect, call dialog.close() and wrongly close
  // the modal mid-interaction.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    previousFocusRef.current = document.activeElement as HTMLElement;
    dialog.showModal();
    const focusable = dialog.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    focusable?.focus();

    // Escape closes the modal, BUT not when it is merely dismissing an
    // open <select> dropdown (target is the SELECT). Listening on the
    // dialog (not document) and skipping SELECT targets prevents picking
    // a category option from closing the whole modal.
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      const target = event.target as HTMLElement | null;
      if (target && target.tagName === "SELECT") return;
      event.preventDefault();
      onCloseRef.current();
    };
    dialog.addEventListener("keydown", onKeyDown);

    const opener = previousFocusRef.current;
    return () => {
      dialog.removeEventListener("keydown", onKeyDown);
      dialog.close();
      opener?.focus();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const titleId = "modal-title";

  const handleCancel = (event: React.SyntheticEvent<HTMLDialogElement>) => {
    event.preventDefault();
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      aria-modal="true"
      aria-labelledby={titleId}
      className="rounded-lg border-none p-0 shadow-xl backdrop:bg-black/50"
      onCancel={handleCancel}
      onClose={onClose}
    >
      <div className="min-w-80 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 id={titleId} className="text-lg font-semibold">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label={t("ui.close")}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}
