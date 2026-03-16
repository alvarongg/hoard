import { fetchApi, toSnakeCase } from "./api";
import type { MainCategory, SubCategory } from "../types/category";

interface MainCategoryCreate {
  name: string;
  description?: string;
  icon?: string;
  displayOrder?: number;
}

interface SubCategoryCreate {
  name: string;
  description?: string;
  icon?: string;
  displayOrder?: number;
}

export const categoriesApi = {
  listMain: (skip = 0, limit = 100): Promise<MainCategory[]> =>
    fetchApi<MainCategory[]>(`/categories?skip=${skip}&limit=${limit}`),

  listSub: (mainCategoryId: string): Promise<SubCategory[]> =>
    fetchApi<SubCategory[]>(`/categories/${mainCategoryId}/subcategories`),

  createMain: (data: MainCategoryCreate): Promise<MainCategory> =>
    fetchApi<MainCategory>("/categories", {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  createSub: (
    mainCategoryId: string,
    data: SubCategoryCreate,
  ): Promise<SubCategory> =>
    fetchApi<SubCategory>(`/categories/${mainCategoryId}/subcategories`, {
      method: "POST",
      body: JSON.stringify(toSnakeCase(data)),
    }),
};
