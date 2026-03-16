export interface MainCategory {
  id: string;
  name: string;
  description: string | null;
  icon: string | null;
  displayOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SubCategory {
  id: string;
  mainCategoryId: string;
  name: string;
  description: string | null;
  icon: string | null;
  displayOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}
