export type SupplierType =
  | "online"
  | "physical_store"
  | "marketplace"
  | "private_seller"
  | "auction";

export interface Supplier {
  id: string;
  name: string;
  type: SupplierType | null;
  country: string | null;
  stateProvince: string | null;
  city: string | null;
  address: string | null;
  postalCode: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  marketplaceUrl: string | null;
  socialMedia: Record<string, unknown> | null;
  rating: number | null;
  notes: string | null;
  isFavorite: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SupplierCreate {
  name: string;
  type?: SupplierType | null;
  country?: string | null;
  stateProvince?: string | null;
  city?: string | null;
  address?: string | null;
  postalCode?: string | null;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
  marketplaceUrl?: string | null;
  socialMedia?: Record<string, unknown> | null;
  rating?: number | null;
  notes?: string | null;
  isFavorite?: boolean;
  isActive?: boolean;
}

export interface SupplierUpdate {
  name?: string | null;
  type?: SupplierType | null;
  country?: string | null;
  stateProvince?: string | null;
  city?: string | null;
  address?: string | null;
  postalCode?: string | null;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
  marketplaceUrl?: string | null;
  socialMedia?: Record<string, unknown> | null;
  rating?: number | null;
  notes?: string | null;
  isFavorite?: boolean;
  isActive?: boolean;
}

export interface SupplierPurchase {
  collectionItemId: string;
  title: string;
  purchaseDate: string | null;
  purchasePrice: number | null;
  purchaseCurrency: string;
}

export interface SupplierReferences {
  collectionItems: number;
  wishlistSightings: number;
  accessories: number;
  readonly total: number;
}
