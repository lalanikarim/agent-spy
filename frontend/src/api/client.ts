import axios from 'axios';
import type {
  RootRunsResponse,
  RunHierarchyResponse,
  DashboardSummary,
  TraceFilters,
  PaginationParams
} from '../types/traces';

// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
      params: config.params,
      data: config.data,
    });
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', {
      status: error.response?.status,
      message: error.response?.data?.detail || error.message,
      url: error.config?.url,
    });
    return Promise.reject(error);
  }
);

// API functions
export const tracesApi = {
  // Get root traces for master table
  getRootTraces: async (
    filters: TraceFilters = {},
    pagination: PaginationParams = { limit: 50, offset: 0 }
  ): Promise<RootRunsResponse> => {
    const params = {
      ...filters,
      ...pagination,
    };
    
    const response = await apiClient.get<RootRunsResponse>('/dashboard/runs/roots', { params });
    return response.data;
  },

  // Get complete trace hierarchy
  getTraceHierarchy: async (traceId: string): Promise<RunHierarchyResponse> => {
    const response = await apiClient.get<RunHierarchyResponse>(`/dashboard/runs/${traceId}/hierarchy`);
    return response.data;
  },

  // Get dashboard statistics
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>('/dashboard/stats/summary');
    return response.data;
  },

  // Health check
  getHealth: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await apiClient.get('http://localhost:8000/health');
    return response.data;
  },
};

export default apiClient;
