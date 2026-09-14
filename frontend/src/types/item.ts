export type ItemCondition =
  | "mint"
  | "near_mint"
  | "excellent"
  | "good"
  | "fair"
  | "poor";

export type AcquisitionType =
  | "purchase"
  | "gift"
  | "trade"
  | "found"
  | "inherited";

export interface CollectionItem {
  id: string;
  collectionId: string;
  catalogItemId: string;
  condition: ItemCondition;
  isComplete: boolean;
  notes: string | null;
  purchasePrice: number | null;
  purchaseCurrency: string;
  purchaseDate: string | null;
  acquisitionType: AcquisitionType | null;
  storageLocation: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CollectionItemCreate {
  catalogItemId: string;
  condition: ItemCondition;
  isComplete?: boolean;
  notes?: string;
  purchasePrice?: number;
  purchaseCurrency?: string;
  purchaseDate?: string;
  acquisitionType?: AcquisitionType;
  storageLocation?: string;
}

export interface CollectionItemUpdate {
  condition?: ItemCondition;
  isComplete?: boolean;
  notes?: string;
  purchasePrice?: number;
  purchaseCurrency?: string;
  purchaseDate?: string;
  acquisitionType?: AcquisitionType;
  storageLocation?: string;
}

export interface CatalogItem {
  id: string;
  catalogId: string;
  title: string;
  subtitle: string | null;
  description: string | null;
  releaseDate: string | null;
  manufacturer: string | null;
  publisher: string | null;
  developer: string | null;
  brand: string | null;
  language: string | null;
  region: string | null;
  rarity: string | null;
  customFields: Record<string, unknown>;
  coverImageUrl: string | null;
  createdAt: string;
  updatedAt: string;
}
export interface CatalogItemCreate {
  title: string;
  subtitle?: string;
  description?: string;
  manufacturer?: string;
  publisher?: string;
  developer?: string;
  brand?: string;
  language?: string;
  region?: string;
  rarity?: string;
  customFields?: Record<string, unknown>;
  coverImageUrl?: string;
}
