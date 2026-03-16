export interface ItemImage {
  id: string;
  collectionItemId: string;
  filePath: string;
  fileName: string;
  fileSize: number | null;
  mimeType: string | null;
  imageType: string | null;
  description: string | null;
  isPrimary: boolean;
  uploadedAt: string;
}
