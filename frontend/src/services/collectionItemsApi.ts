import { fetchApi, toSnakeCase } from "./api";
import type {
  CollectionItem,
  CollectionItemCreate,
  CollectionItemUpdate,
} from "../types/item";

export const collectionItemsApi = {
  list: (collectionId: string, skip = 0, limit = 100): Promise<CollectionItem[]> =>
    fetchApi<CollectionItem[]>(
      `/collections/${collectionId}/items?skip=${skip}&limit=${limit}`,
    ),

  add: (collectionId: string, data: CollectionItemCreate): Promise<CollectionItem> =>
    fetchApi<CollectionItem>(`/collections/${collectionId}/items`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  update: (id: string, data: CollectionItemUpdate): Promise<CollectionItem> =>
    fetchApi<CollectionItem>(`/items/${id}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  delete: (id: string): Promise<void> =>
    fetchApi<void>(`/items/${id}`, { method: "DELETE" }),
};
