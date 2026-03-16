import { fetchApi, toSnakeCase } from "./api";
import type {
  Collection,
  CollectionCreate,
  CollectionUpdate,
} from "../types/collection";

export const collectionsApi = {
  list: (skip = 0, limit = 100): Promise<Collection[]> =>
    fetchApi<Collection[]>(`/collections?skip=${skip}&limit=${limit}`),

  getById: (id: string): Promise<Collection> =>
    fetchApi<Collection>(`/collections/${id}`),

  create: (data: CollectionCreate): Promise<Collection> =>
    fetchApi<Collection>("/collections", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  update: (id: string, data: CollectionUpdate): Promise<Collection> =>
    fetchApi<Collection>(`/collections/${id}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  delete: (id: string): Promise<void> =>
    fetchApi<void>(`/collections/${id}`, { method: "DELETE" }),
};
