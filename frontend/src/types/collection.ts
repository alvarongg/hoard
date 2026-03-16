export type CollectionType = "single_category" | "multi_category" | "mixed";

export type DisplayOrder =
  | "alphabetical"
  | "release_date"
  | "acquisition_date"
  | "custom"
  | "value"
  | "category";

export interface Collection {
  id: string;
  name: string;
  description: string | null;
  collectionType: CollectionType;
  theme: string | null;
  themeDescription: string | null;
  restrictedToSubCategoryId: string | null;
  goalDescription: string | null;
  goalItemsCount: number | null;
  displayOrder: DisplayOrder;
  isPublic: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CollectionCreate {
  name: string;
  description?: string;
  collectionType: CollectionType;
  theme?: string;
  restrictedToSubCategoryId?: string;
  goalDescription?: string;
  goalItemsCount?: number;
  displayOrder?: DisplayOrder;
  isPublic?: boolean;
}

export interface CollectionUpdate {
  name?: string;
  description?: string;
  theme?: string;
  goalDescription?: string;
  goalItemsCount?: number;
  displayOrder?: DisplayOrder;
  isPublic?: boolean;
  isActive?: boolean;
}
