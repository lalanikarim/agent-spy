import axios from "axios";
import { config, logConfiguration } from "../config/environment";
import type {
  DashboardSummary,
  PaginationParams,
  RootRunsResponse,
  RunHierarchyResponse,
  TraceFilters,
} from "../types/traces";

// Log configuration in development
logConfiguration();

// API client configuration using centralized config
const API_BASE_URL = config.apiBaseUrl;

// Immediate logging when API client module loads
console.log("🚀 API Client module loaded!");
console.log("🔧 API Client config:", {
  baseURL: API_BASE_URL,
  timeout: 10000,
});

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`,
      {
        baseURL: config.baseURL,
        fullURL: `${config.baseURL}${config.url}`,
        params: config.params,
        data: config.data,
        headers: config.headers,
      }
    );
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    console.error("Request config:", error.config);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`, {
      status: response.status,
      statusText: response.statusText,
      dataLength: JSON.stringify(response.data).length,
      dataPreview: JSON.stringify(response.data).substring(0, 200) + "...",
    });
    return response;
  },
  (error) => {
    console.error("❌ API Response Error:", {
      status: error.response?.status,
      statusText: error.response?.statusText,
      message: error.response?.data?.detail || error.message,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      fullURL: error.config
        ? `${error.config.baseURL}${error.config.url}`
        : "unknown",
      errorCode: error.code,
      errorMessage: error.message,
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

    const response = await apiClient.get<RootRunsResponse>(
      "/dashboard/runs/roots",
      { params }
    );
    return response.data;
  },

  // Get complete trace hierarchy
  getTraceHierarchy: async (traceId: string): Promise<RunHierarchyResponse> => {
    const response = await apiClient.get<RunHierarchyResponse>(
      `/dashboard/runs/${traceId}/hierarchy`
    );
    return response.data;
  },

  // Get dashboard statistics
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>(
      "/dashboard/stats/summary"
    );
    return response.data;
  },

  // Health check - now uses relative path instead of hardcoded URL
  getHealth: async (): Promise<{ status: string; timestamp: string }> => {
    console.log("🏥 Health check initiated...");
    console.log("🔧 Health check config:", {
      apiBaseUrl: config.apiBaseUrl,
      baseUrlWithoutApi: config.apiBaseUrl.replace("/api/v1", ""),
      healthUrl: `${config.apiBaseUrl.replace("/api/v1", "")}/health`,
    });

    // Create a separate axios instance for health check since it's not under /api/v1
    const healthClient = axios.create({
      baseURL: config.apiBaseUrl.replace("/api/v1", ""),
      timeout: 5000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add logging to health client
    healthClient.interceptors.request.use(
      (config) => {
        console.log("🏥 Health Request:", {
          method: config.method,
          url: config.url,
          baseURL: config.baseURL,
          fullURL: `${config.baseURL}${config.url}`,
        });
        return config;
      },
      (error) => {
        console.error("🏥 Health Request Error:", error);
        return Promise.reject(error);
      }
    );

    healthClient.interceptors.response.use(
      (response) => {
        console.log("🏥 Health Response:", {
          status: response.status,
          data: response.data,
        });
        return response;
      },
      (error) => {
        console.error("🏥 Health Response Error:", {
          status: error.response?.status,
          message: error.message,
          code: error.code,
        });
        return Promise.reject(error);
      }
    );

    const response = await healthClient.get("/health");
    console.log("🏥 Health check completed successfully");
    return response.data;
  },
};

export default apiClient;
