// Types for Agent Spy dashboard

export interface TraceRun {
  id: string;
  name: string;
  run_type: string;
  status: 'running' | 'completed' | 'failed';
  start_time: string;
  end_time?: string | null;
  parent_run_id?: string | null;
  inputs?: Record<string, any> | null;
  outputs?: Record<string, any> | null;
  error?: string | null;
  extra?: Record<string, any> | null;
  tags?: string[] | null;
  project_name?: string | null;
  duration_ms?: number | null;
}

export interface RootRunsResponse {
  runs: TraceRun[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface RunHierarchyNode {
  id: string;
  name: string;
  run_type: string;
  status: 'running' | 'completed' | 'failed';
  start_time?: string | null;
  end_time?: string | null;
  parent_run_id?: string | null;
  inputs?: Record<string, any> | null;
  outputs?: Record<string, any> | null;
  error?: string | null;
  extra?: Record<string, any> | null;
  tags?: string[] | null;
  duration_ms?: number | null;
  children: RunHierarchyNode[];
}

export interface RunHierarchyResponse {
  root_run_id: string;
  hierarchy: RunHierarchyNode;
  total_runs: number;
  max_depth: number;
}

export interface DashboardStats {
  total_runs: number;
  total_traces: number;
  recent_runs_24h: number;
  status_distribution: Record<string, number>;
  run_type_distribution: Record<string, number>;
  project_distribution: Record<string, number>;
}

export interface ProjectInfo {
  name: string;
  total_runs: number;
  total_traces: number;
  last_activity?: string | null;
}

export interface DashboardSummary {
  stats: DashboardStats;
  recent_projects: ProjectInfo[];
  timestamp: string;
}

// Filter types
export interface TraceFilters {
  project_name?: string;
  status?: string;
  search?: string;
  start_time_gte?: string;
  start_time_lte?: string;
}

export interface PaginationParams {
  limit: number;
  offset: number;
}
