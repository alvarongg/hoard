export type TimelinePeriod = "month" | "quarter" | "year";

export interface ValuationStats {
  totalInvested: string;
  currentValue: string;
  valueGain: string;
  roiPercentage: string | null;
}

export interface DashboardStats {
  totalCollections: number;
  totalItems: number;
  totalInvested: string;
  currentValue: string;
  valueGain: string;
  roiPercentage: string | null;
  completeItems: number;
  gradedItems: number;
}

export interface CollectionStatsEntry {
  collectionId: string;
  collectionName: string;
  totalItems: number;
  totalInvested: string;
  currentValue: string;
  roiPercentage: string | null;
}

export interface CategoryStatsEntry {
  subCategoryId: string | null;
  subCategoryName: string;
  itemCount: number;
  currentValue: string;
}

export interface TimelineEntry {
  period: string;
  itemCount: number;
  invested: string;
}
