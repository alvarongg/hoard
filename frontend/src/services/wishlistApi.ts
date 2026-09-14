import { fetchApi, toSnakeCase } from "./api";
import type {
  WishlistItem,
  WishlistItemCreate,
  WishlistItemUpdate,
  WishlistItemDetail,
  WishlistAcquire,
  Sighting,
  SightingCreate,
  SightingUpdate,
} from "../types/wishlist";

export interface WishlistFilters {
  collectionId?: string;
  priority?: number;
  urgency?: string;
  isActive?: boolean;
  includeAcquired?: boolean;
}

export const wishlistApi = {
  list: (filters?: WishlistFilters): Promise<WishlistItem[]> => {
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
    const endpoint = queryString ? `/wishlist?${queryString}` : "/wishlist";

    return fetchApi<WishlistItem[]>(endpoint);
  },

  get: (id: string): Promise<WishlistItemDetail> =>
    fetchApi<WishlistItemDetail>(`/wishlist/${id}`),

  create: (data: WishlistItemCreate): Promise<WishlistItem> =>
    fetchApi<WishlistItem>("/wishlist", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  update: (id: string, data: WishlistItemUpdate): Promise<WishlistItem> =>
    fetchApi<WishlistItem>(`/wishlist/${id}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  remove: (id: string): Promise<void> =>
    fetchApi<void>(`/wishlist/${id}`, { method: "DELETE" }),

  acquire: (id: string, data: WishlistAcquire): Promise<WishlistItem> =>
    fetchApi<WishlistItem>(`/wishlist/${id}/acquire`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  // Sightings
  listSightings: (wishlistItemId: string): Promise<Sighting[]> =>
    fetchApi<Sighting[]>(`/wishlist/${wishlistItemId}/sightings`),

  createSighting: (wishlistItemId: string, data: Omit<SightingCreate, "wishlistItemId">): Promise<Sighting> =>
    fetchApi<Sighting>(`/wishlist/${wishlistItemId}/sightings`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  updateSighting: (sightingId: string, data: SightingUpdate): Promise<Sighting> =>
    fetchApi<Sighting>(`/sightings/${sightingId}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  removeSighting: (sightingId: string): Promise<void> =>
    fetchApi<void>(`/sightings/${sightingId}`, { method: "DELETE" }),
};
