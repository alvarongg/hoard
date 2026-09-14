import { fetchApi, toSnakeCase } from "./api";
import type {
  Supplier,
  SupplierCreate,
  SupplierUpdate,
  SupplierPurchase,
} from "../types/supplier";

export interface SupplierFilters {
  type?: string;
  country?: string;
  isFavorite?: boolean;
  isActive?: boolean;
  search?: string;
}

export const suppliersApi = {
  list: (filters?: SupplierFilters): Promise<Supplier[]> => {
    const params = new URLSearchParams();

    if (filters) {
      const snakeFilters = toSnakeCase<Record<string, unknown>>(filters);
      for (const [key, value] of Object.entries(snakeFilters)) {
        if (value !== undefined && value !== null && value !== "") {
          params.append(key, String(value));
        }
      }
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/suppliers?${queryString}` : "/suppliers";

    return fetchApi<Supplier[]>(endpoint);
  },

  get: (id: string): Promise<Supplier> =>
    fetchApi<Supplier>(`/suppliers/${id}`),

  create: (data: SupplierCreate): Promise<Supplier> =>
    fetchApi<Supplier>("/suppliers", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  update: (id: string, data: SupplierUpdate): Promise<Supplier> =>
    fetchApi<Supplier>(`/suppliers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  remove: (id: string): Promise<void> =>
    fetchApi<void>(`/suppliers/${id}`, { method: "DELETE" }),

  purchases: (id: string): Promise<SupplierPurchase[]> =>
    fetchApi<SupplierPurchase[]>(`/suppliers/${id}/purchases`),
};
