import { fetchApi } from "./api";
import type {
  DashboardStats,
  ValuationStats,
  CollectionStatsEntry,
  CategoryStatsEntry,
  TimelineEntry,
  TimelinePeriod,
} from "../types/stats";

export const statsApi = {
  dashboard: (): Promise<DashboardStats> =>
    fetchApi<DashboardStats>("/stats/dashboard"),

  valuation: (): Promise<ValuationStats> =>
    fetchApi<ValuationStats>("/stats/valuation"),

  collections: (): Promise<CollectionStatsEntry[]> =>
    fetchApi<CollectionStatsEntry[]>("/stats/collections"),

  categories: (): Promise<CategoryStatsEntry[]> =>
    fetchApi<CategoryStatsEntry[]>("/stats/categories"),

  timeline: (period: TimelinePeriod = "month"): Promise<TimelineEntry[]> =>
    fetchApi<TimelineEntry[]>(`/stats/timeline?period=${period}`),
};
