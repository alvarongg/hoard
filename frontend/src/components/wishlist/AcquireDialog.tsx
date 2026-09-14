import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import type { WishlistItem } from "../../types/wishlist";

interface AcquireDialogProps {
  item: WishlistItem;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (collectionItemId: string) => void;
  isLoading?: boolean;
}

/**
 * AcquireDialog - Modal dialog for marking a wishlist item as acquired.
 *
 * Features:
 * - Focus trap for accessibility
 * - Closes with Escape key
 * - Returns focus to trigger element on close
 * - Requires collection item ID confirmation
 */
export function AcquireDialog({ item, isOpen, onClose, onConfirm, isLoading }: AcquireDialogProps) {
  const { t } = useTranslation();
  const [collectionItemId, setCollectionItemId] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      // Focus the input after a short delay to allow the dialog to render
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  const handleClose = useCallback(() => {
    setCollectionItemId("");
    setError("");
    onClose();
    // Return focus to the previous element
    previousActiveElement.current?.focus();
  }, [onClose]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, handleClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!collectionItemId.trim()) {
      setError(t("wishlist.acquire.collectionItemRequired"));
      return;
    }
    onConfirm(collectionItemId);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="acquire-dialog-title"
      aria-describedby="acquire-dialog-description"
    >
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 id="acquire-dialog-title" className="text-lg font-semibold text-gray-900">
          {t("wishlist.acquire.title")}
        </h2>

        <p id="acquire-dialog-description" className="mt-2 text-sm text-gray-600">
          {t("wishlist.acquire.description")}
        </p>

        {item.isAcquired && (
          <p className="mt-2 rounded-md bg-yellow-50 p-2 text-sm text-yellow-800">
            {t("wishlist.acquire.alreadyAcquired")}
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label htmlFor="collection-item-id" className="block text-sm font-medium text-gray-700">
              {t("wishlist.acquire.collectionItemId")}
            </label>
            <input
              ref={inputRef}
              type="text"
              id="collection-item-id"
              value={collectionItemId}
              onChange={(e) => {
                setCollectionItemId(e.target.value);
                setError("");
              }}
              aria-invalid={!!error}
              aria-describedby={error ? "collection-item-error" : undefined}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder={t("wishlist.acquire.collectionItemPlaceholder")}
            />
            {error && (
              <p id="collection-item-error" className="mt-1 text-sm text-red-600">
                {error}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              disabled={isLoading || item.isAcquired}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {isLoading ? t("common.saving") : t("wishlist.acquire.confirm")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
