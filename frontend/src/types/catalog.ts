export interface Catalog {
  id: string;
  subCategoryId: string;
  name: string;
  description: string | null;
  totalItems: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CatalogCreate {
  subCategoryId: string;
  name: string;
  description?: string;
}

export interface CatalogUpdate {
  name?: string;
  description?: string;
  isActive?: boolean;
}
