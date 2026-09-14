import { useQuery } from "@tanstack/react-query";
import { statsApi } from "../services/statsApi";
import type {
  DashboardStats,
  ValuationStats,
  CollectionStatsEntry,
  CategoryStatsEntry,
  TimelineEntry,
  TimelinePeriod,
} from "../types/stats";

const STATS_KEY = ["collection-stats"] as const;

export function useDashboardStats() {
  return useQuery<DashboardStats, Error>({
    queryKey: [...STATS_KEY, "dashboard"],
    queryFn: () => statsApi.dashboard(),
  });
}

export function useValuationStats() {
  return useQuery<ValuationStats, Error>({
    queryKey: [...STATS_KEY, "valuation"],
    queryFn: () => statsApi.valuation(),
  });
}

export function useCollectionStatsList() {
  return useQuery<CollectionStatsEntry[], Error>({
    queryKey: [...STATS_KEY, "collections"],
    queryFn: () => statsApi.collections(),
  });
}

export function useCategoryStats() {
  return useQuery<CategoryStatsEntry[], Error>({
    queryKey: [...STATS_KEY, "categories"],
    queryFn: () => statsApi.categories(),
  });
}

export function useTimelineStats(period: TimelinePeriod = "month") {
  return useQuery<TimelineEntry[], Error>({
    queryKey: [...STATS_KEY, "timeline", period],
    queryFn: () => statsApi.timeline(period),
  });
}
