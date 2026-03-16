import { useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../ui/Button";

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface ImageUploadProps {
  onUpload: (file: File) => void;
  isLoading: boolean;
}

export function ImageUpload({ onUpload, isLoading }: ImageUploadProps) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  function validateFile(file: File): string | null {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return t("images.invalidType");
    }
    if (file.size > MAX_FILE_SIZE) {
      return t("images.tooLarge");
    }
    return null;
  }

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        setPreview(null);
        setSelectedFile(null);
        return;
      }

      setError(null);
      setSelectedFile(file);

      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  function handleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) handleFile(file);
  }

  function handleDrop(event: React.DragEvent) {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleDragOver(event: React.DragEvent) {
    event.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleUploadClick() {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  }

  return (
    <div className="space-y-3">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleInputChange}
        className="sr-only"
        aria-label={t("images.upload")}
      />
      <div
        role="button"
        tabIndex={0}
        aria-label={t("images.dropzone")}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
          isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <p className="text-sm text-gray-600">{t("images.dropzone")}</p>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      {preview && (
        <div className="space-y-2">
          <img
            src={preview}
            alt={t("images.preview")}
            className="h-40 w-auto rounded-md object-cover"
          />
          <Button onClick={handleUploadClick} isLoading={isLoading}>
            {t("images.upload")}
          </Button>
        </div>
      )}
    </div>
  );
}
