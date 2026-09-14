import { useEffect, useRef, useCallback } from "react";
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

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    previousFocusRef.current = document.activeElement as HTMLElement;
    dialog.showModal();
    // Move focus into the dialog's first focusable element for a
    // predictable entry point (native showModal otherwise focuses the
    // dialog itself). The native <dialog> contains focus while open.
    const focusable = dialog.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    focusable?.focus();
    document.addEventListener("keydown", handleKeyDown);

    const opener = previousFocusRef.current;
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      dialog.close();
      // Return focus to whatever opened the dialog.
      opener?.focus();
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const titleId = "modal-title";

  return (
    <dialog
      ref={dialogRef}
      aria-modal="true"
      aria-labelledby={titleId}
      className="rounded-lg border-none p-0 shadow-xl backdrop:bg-black/50"
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
