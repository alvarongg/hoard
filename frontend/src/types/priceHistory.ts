export interface PriceHistoryEntry {
  id: string;
  catalogItemId: string;
  condition: string;
  isComplete: boolean;
  completenessDescription: string | null;
  price: string;
  currency: string;
  source: string | null;
  sourceUrl: string | null;
  priceDate: string;
  region: string | null;
  notes: string | null;
  recordedAt: string;
}

export interface PriceHistoryCreate {
  condition: string;
  isComplete?: boolean;
  completenessDescription?: string | null;
  price: string;
  currency?: string;
  source?: string | null;
  sourceUrl?: string | null;
  priceDate: string;
  region?: string | null;
  notes?: string | null;
}

export interface LatestPriceEntry {
  condition: string;
  isComplete: boolean;
  price: string;
  currency: string;
  priceDate: string;
  source: string | null;
}

export interface ValueUpdateResult {
  updated: boolean;
  currentMarketValue: string | null;
  valueSource: string | null;
  reason: string | null;
}

export interface PriceHistoryFilters {
  condition?: string;
  isComplete?: boolean;
  region?: string;
  dateFrom?: string;
  dateTo?: string;
}
