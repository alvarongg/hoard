import { fetchApi } from "./api";
import type { ItemImage } from "../types/image";

export const imagesApi = {
  list: (itemId: string): Promise<ItemImage[]> =>
    fetchApi<ItemImage[]>(`/items/${itemId}/images`),

  upload: async (itemId: string, file: File): Promise<ItemImage> => {
    const formData = new FormData();
    formData.append("file", file);

    return fetchApi<ItemImage>(`/items/${itemId}/images`, {
      method: "POST",
      body: formData,
    });
  },

  delete: (imageId: string): Promise<void> =>
    fetchApi<void>(`/images/${imageId}`, { method: "DELETE" }),
};
