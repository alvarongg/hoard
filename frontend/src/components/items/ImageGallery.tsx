import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ItemImage } from "../../types/image";
import { EmptyState } from "../ui/EmptyState";

interface ImageGalleryProps {
  images: ItemImage[];
  onDelete?: (imageId: string) => void;
}

export function ImageGallery({ images, onDelete }: ImageGalleryProps) {
  const { t } = useTranslation();
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  if (images.length === 0) {
    return <EmptyState title={t("images.empty")} />;
  }

  function closeLightbox() {
    setLightboxIndex(null);
  }

  return (
    <>
      <div
        role="list"
        aria-label={t("images.gallery")}
        className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4"
      >
        {images.map((image, index) => (
          <div key={image.id} role="listitem" className="relative">
            <button
              type="button"
              onClick={() => setLightboxIndex(index)}
              className="w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md"
              aria-label={image.fileName}
            >
              <img
                src={image.filePath}
                alt={image.description ?? image.fileName}
                className="h-32 w-full rounded-md object-cover"
                loading="lazy"
              />
            </button>
            {image.isPrimary && (
              <span className="absolute left-1 top-1 rounded bg-blue-600 px-1.5 py-0.5 text-xs text-white">
                {t("images.primary")}
              </span>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(image.id)}
                aria-label={t("images.delete")}
                className="absolute right-1 top-1 rounded bg-red-600 px-1.5 py-0.5 text-xs text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>

      {lightboxIndex !== null && images[lightboxIndex] && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={images[lightboxIndex]!.fileName}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={closeLightbox}
          onKeyDown={(e) => {
            if (e.key === "Escape") closeLightbox();
          }}
        >
          <button
            onClick={closeLightbox}
            aria-label={t("ui.close")}
            className="absolute right-4 top-4 rounded-full bg-white/20 p-2 text-white hover:bg-white/40 focus:outline-none focus:ring-2 focus:ring-white"
          >
            ✕
          </button>
          <img
            src={images[lightboxIndex]!.filePath}
            alt={
              images[lightboxIndex]!.description ??
              images[lightboxIndex]!.fileName
            }
            className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
          />
        </div>
      )}
    </>
  );
}
