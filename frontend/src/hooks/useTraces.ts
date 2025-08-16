import type { UseQueryResult } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { tracesApi } from "../api/client";
import type {
  DashboardSummary,
  PaginationParams,
  RootRunsResponse,
  RunHierarchyResponse,
  TraceFilters,
} from "../types/traces";

// Query keys
export const QUERY_KEYS = {
  rootTraces: "rootTraces",
  traceHierarchy: "traceHierarchy",
  dashboardSummary: "dashboardSummary",
  health: "health",
} as const;

// Custom hooks for data fetching
export const useRootTraces = (
  filters: TraceFilters = {},
  pagination: PaginationParams = { limit: 50, offset: 0 },
  options?: { enabled?: boolean; refetchInterval?: number }
): UseQueryResult<RootRunsResponse, Error> => {
  return useQuery({
    queryKey: [QUERY_KEYS.rootTraces, filters, pagination],
    queryFn: () => tracesApi.getRootTraces(filters, pagination),
    staleTime: 30000, // 30 seconds
    refetchInterval: options?.refetchInterval || 60000, // Refetch every minute
    enabled: options?.enabled !== false,
  });
};

export const useTraceHierarchy = (
  traceId: string | null,
  options?: { enabled?: boolean }
): UseQueryResult<RunHierarchyResponse, Error> => {
  return useQuery({
    queryKey: [QUERY_KEYS.traceHierarchy, traceId],
    queryFn: () => tracesApi.getTraceHierarchy(traceId!),
    staleTime: 60000, // 1 minute
    enabled: !!traceId && options?.enabled !== false,
  });
};

export const useDashboardSummary = (options?: {
  enabled?: boolean;
  refetchInterval?: number;
}): UseQueryResult<DashboardSummary, Error> => {
  return useQuery({
    queryKey: [QUERY_KEYS.dashboardSummary],
    queryFn: () => tracesApi.getDashboardSummary(),
    staleTime: 60000, // 1 minute
    refetchInterval: options?.refetchInterval || 120000, // Refetch every 2 minutes
    enabled: options?.enabled !== false,
  });
};

export const useHealth = (options?: {
  enabled?: boolean;
  refetchInterval?: number;
}): UseQueryResult<{ status: string; timestamp: string }, Error> => {
  console.log("🏥 useHealth hook called with options:", options);
  return useQuery({
    queryKey: [QUERY_KEYS.health],
    queryFn: () => {
      console.log("🏥 useHealth queryFn executing...");
      return tracesApi.getHealth();
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: options?.refetchInterval || 30000, // Refetch every 30 seconds
    enabled: options?.enabled !== false,
    onSuccess: (data) => {
      console.log("🏥 useHealth success:", data);
    },
    onError: (error) => {
      console.error("🏥 useHealth error:", error);
    },
  });
};
