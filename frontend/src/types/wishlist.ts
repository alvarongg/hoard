export type Urgency = "low" | "medium" | "high" | "critical";
export type Priority = 1 | 2 | 3 | 4 | 5;
export type SightingDecision = "buy" | "pass" | "wait" | "negotiate";

export interface WishlistItem {
  id: string;
  collectionId: string;
  catalogItemId: string;
  desiredCondition: string | null;
  desiredConditionMin: string | null;
  mustBeComplete: boolean;
  desiredCompletenessDescription: string | null;
  maxPrice: number | null;
  currency: string;
  specificVariantRequired: boolean;
  variantDescription: string | null;
  priority: Priority;
  urgency: Urgency;
  notes: string | null;
  searchNotes: string | null;
  tags: string[] | null;
  isActive: boolean;
  isAcquired: boolean;
  acquiredDate: string | null;
  acquiredCollectionItemId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface WishlistItemCreate {
  collectionId: string;
  catalogItemId: string;
  desiredCondition?: string | null;
  desiredConditionMin?: string | null;
  mustBeComplete?: boolean;
  desiredCompletenessDescription?: string | null;
  maxPrice?: number | null;
  currency?: string;
  specificVariantRequired?: boolean;
  variantDescription?: string | null;
  priority?: Priority;
  urgency?: Urgency;
  notes?: string | null;
  searchNotes?: string | null;
  tags?: string[] | null;
  isActive?: boolean;
}

export interface WishlistItemUpdate {
  desiredCondition?: string | null;
  desiredConditionMin?: string | null;
  mustBeComplete?: boolean;
  desiredCompletenessDescription?: string | null;
  maxPrice?: number | null;
  currency?: string;
  specificVariantRequired?: boolean;
  variantDescription?: string | null;
  priority?: Priority;
  urgency?: Urgency;
  notes?: string | null;
  searchNotes?: string | null;
  tags?: string[] | null;
  isActive?: boolean;
}

export interface PriceAggregates {
  avgPrice: number | null;
  minPrice: number | null;
  maxPrice: number | null;
  totalSightings: number;
  availableSightings: number;
}

export interface WishlistItemDetail extends WishlistItem {
  priceAggregates: PriceAggregates;
}

export interface WishlistAcquire {
  acquiredCollectionItemId: string;
}

export interface Sighting {
  id: string;
  wishlistItemId: string;
  sightedAt: string | null;
  supplierId: string | null;
  locationDescription: string | null;
  url: string | null;
  price: number;
  currency: string;
  condition: string | null;
  isComplete: boolean | null;
  description: string | null;
  imageUrls: string[] | null;
  isAvailable: boolean;
  quantityAvailable: number;
  lastCheckedAt: string | null;
  contacted: boolean;
  contactedAt: string | null;
  contactMethod: string | null;
  responseNotes: string | null;
  decision: SightingDecision | null;
  decisionNotes: string | null;
  decisionDate: string | null;
  createdAt: string;
}

export interface SightingCreate {
  wishlistItemId: string;
  sightedAt?: string | null;
  supplierId?: string | null;
  locationDescription?: string | null;
  url?: string | null;
  price: number;
  currency?: string;
  condition?: string | null;
  isComplete?: boolean | null;
  description?: string | null;
  imageUrls?: string[] | null;
  isAvailable?: boolean;
  quantityAvailable?: number;
  lastCheckedAt?: string | null;
  contacted?: boolean;
  contactedAt?: string | null;
  contactMethod?: string | null;
  responseNotes?: string | null;
  decision?: SightingDecision | null;
  decisionNotes?: string | null;
  decisionDate?: string | null;
}

export interface SightingUpdate {
  sightedAt?: string | null;
  supplierId?: string | null;
  locationDescription?: string | null;
  url?: string | null;
  price?: number;
  currency?: string;
  condition?: string | null;
  isComplete?: boolean | null;
  description?: string | null;
  imageUrls?: string[] | null;
  isAvailable?: boolean;
  quantityAvailable?: number;
  lastCheckedAt?: string | null;
  contacted?: boolean;
  contactedAt?: string | null;
  contactMethod?: string | null;
  responseNotes?: string | null;
  decision?: SightingDecision | null;
  decisionNotes?: string | null;
  decisionDate?: string | null;
}
