import { useQuery } from "@tanstack/react-query";
import { categoriesApi } from "../services/categoriesApi";
import type { MainCategory, SubCategory } from "../types/category";

const CATEGORIES_KEY = ["categories"] as const;

export function useMainCategories() {
  const query = useQuery<MainCategory[], Error>({
    queryKey: CATEGORIES_KEY,
    queryFn: () => categoriesApi.listMain(),
  });

  return query;
}

export function useSubCategories(mainCategoryId: string) {
  const query = useQuery<SubCategory[], Error>({
    queryKey: ["categories", mainCategoryId, "subcategories"],
    queryFn: () => categoriesApi.listSub(mainCategoryId),
    enabled: !!mainCategoryId,
  });

  return query;
}
