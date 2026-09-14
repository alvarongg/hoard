import { fetchApi, toSnakeCase } from "./api";
import type {
  Accessory,
  AccessoryCreate,
  AccessoryUpdate,
  LowStockEntry,
  ItemAccessoryAssignment,
} from "../types/accessory";

export const accessoriesApi = {
  list: (category?: string): Promise<Accessory[]> => {
    const qs = category ? `?category=${encodeURIComponent(category)}` : "";
    return fetchApi<Accessory[]>(`/accessories${qs}`);
  },

  get: (id: string): Promise<Accessory> =>
    fetchApi<Accessory>(`/accessories/${id}`),

  create: (data: AccessoryCreate): Promise<Accessory> =>
    fetchApi<Accessory>("/accessories", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  update: (id: string, data: AccessoryUpdate): Promise<Accessory> =>
    fetchApi<Accessory>(`/accessories/${id}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  remove: (id: string): Promise<void> =>
    fetchApi<void>(`/accessories/${id}`, { method: "DELETE" }),

  lowStock: (): Promise<LowStockEntry[]> =>
    fetchApi<LowStockEntry[]>("/accessories/low-stock"),

  listAssignments: (
    collectionItemId: string,
  ): Promise<ItemAccessoryAssignment[]> =>
    fetchApi<ItemAccessoryAssignment[]>(
      `/collection-items/${collectionItemId}/accessories`,
    ),

  assign: (
    collectionItemId: string,
    accessoryId: string,
    quantityUsed: number,
  ): Promise<ItemAccessoryAssignment> =>
    fetchApi<ItemAccessoryAssignment>(
      `/collection-items/${collectionItemId}/accessories`,
      {
        method: "POST",
        body: JSON.stringify(
          toSnakeCase({ accessoryId, quantityUsed }),
        ),
      },
    ),

  unassign: (itemAccessoryId: string): Promise<void> =>
    fetchApi<void>(`/item-accessories/${itemAccessoryId}`, {
      method: "DELETE",
    }),
};
