import axios from 'axios';
import type {
  RootRunsResponse,
  RunHierarchyResponse,
  DashboardSummary,
  TraceFilters,
  PaginationParams
} from '../types/traces';
import { config, logConfiguration } from '../config/environment';

// Log configuration in development
logConfiguration();

// API client configuration using centralized config
const API_BASE_URL = config.apiBaseUrl;

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

  // Health check - now uses relative path instead of hardcoded URL
  getHealth: async (): Promise<{ status: string; timestamp: string }> => {
    // Create a separate axios instance for health check since it's not under /api/v1
    const healthClient = axios.create({
      baseURL: config.apiBaseUrl.replace('/api/v1', ''),
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    const response = await healthClient.get('/health');
    return response.data;
  },
};

export default apiClient;
