/**
 * Environment configuration for Agent Spy frontend
 * Centralizes all environment variable access and provides type safety
 */

interface EnvironmentConfig {
  /** Base URL for API calls (includes /api/v1 suffix) */
  apiBaseUrl: string;
  /** Whether running in development mode */
  isDevelopment: boolean;
  /** Backend server port */
  backendPort: string;
  /** Frontend server port */
  frontendPort: string;
  /** Environment name (development, production, etc.) */
  environment: string;
}

/**
 * Main configuration object using environment variables with fallbacks
 */
export const config: EnvironmentConfig = {
  // Use environment variables first, then fall back to defaults
  apiBaseUrl:
    import.meta.env.VITE_API_BASE_URL || "http://localhost:3001/api/v1",
  isDevelopment: import.meta.env.DEV || false,
  backendPort: import.meta.env.VITE_BACKEND_PORT || "8000",
  frontendPort: import.meta.env.VITE_FRONTEND_PORT || "3001",
  environment: import.meta.env.MODE || "development",
};

// Immediate logging when this module loads
console.log("🔧 Environment module loaded!");
console.log("📋 Raw environment variables:", {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_BACKEND_PORT: import.meta.env.VITE_BACKEND_PORT,
  VITE_FRONTEND_PORT: import.meta.env.VITE_FRONTEND_PORT,
  VITE_BACKEND_HOST: import.meta.env.VITE_BACKEND_HOST,
  DEV: import.meta.env.DEV,
  MODE: import.meta.env.MODE,
});
console.log("⚙️ Config object:", config);

/**
 * Helper to get base URL without /api/v1 suffix
 * Useful for health checks and user-facing error messages
 */
export const getBaseUrl = (): string => {
  return config.apiBaseUrl.replace("/api/v1", "");
};

/**
 * Helper to get health check URL
 * Constructs the full health check endpoint URL
 */
export const getHealthUrl = (): string => {
  return `${getBaseUrl()}/health`;
};

/**
 * Helper to check if we're in a specific environment
 */
export const isEnvironment = (env: string): boolean => {
  return config.environment === env;
};

/**
 * Helper to get backend URL for proxy configuration
 */
export const getBackendUrl = (): string => {
  // Use environment variable for backend host if available, otherwise use localhost
  const backendHost = import.meta.env.VITE_BACKEND_HOST || "localhost";
  return `http://${backendHost}:${config.backendPort}`;
};

/**
 * Debug helper to log current configuration (development only)
 */
export const logConfiguration = (): void => {
  if (config.isDevelopment) {
    console.log("🔧 Agent Spy Frontend Configuration:", {
      apiBaseUrl: config.apiBaseUrl,
      baseUrl: getBaseUrl(),
      healthUrl: getHealthUrl(),
      backendPort: config.backendPort,
      frontendPort: config.frontendPort,
      environment: config.environment,
      isDevelopment: config.isDevelopment,
    });
    console.log("🌐 Network Configuration:", {
      proxyUrl: `http://localhost:${config.frontendPort}/api/v1`,
      directBackendUrl: getBackendUrl() + "/api/v1",
      healthCheckUrl: getHealthUrl(),
      backendHost: import.meta.env.VITE_BACKEND_HOST || "localhost",
    });
    console.log("🔧 Raw Environment Variables:", {
      VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
      VITE_BACKEND_PORT: import.meta.env.VITE_BACKEND_PORT,
      VITE_FRONTEND_PORT: import.meta.env.VITE_FRONTEND_PORT,
      VITE_BACKEND_HOST: import.meta.env.VITE_BACKEND_HOST,
      DEV: import.meta.env.DEV,
      MODE: import.meta.env.MODE,
    });
  }
};
