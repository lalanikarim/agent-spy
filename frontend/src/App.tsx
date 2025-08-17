import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App as AntApp, ConfigProvider } from "antd";
import "./App.css";
import "./styles/theme.css";
import Dashboard from "./components/Dashboard";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";

// Immediate logging when App module loads
console.log("🎯 App module loaded!");
console.log("🔧 App environment check:", {
  NODE_ENV: process.env.NODE_ENV,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_BACKEND_PORT: import.meta.env.VITE_BACKEND_PORT,
  VITE_FRONTEND_PORT: import.meta.env.VITE_FRONTEND_PORT,
});

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 60000, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});

// Ant Design theme configuration component
const AntDesignTheme: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme } = useTheme();
  
  const isDark = theme === 'dark';
  
  const antTheme = {
    token: {
      colorPrimary: isDark ? '#00d4ff' : '#3b82f6',
      colorSuccess: '#10b981',
      colorWarning: '#f59e0b',
      colorError: '#ef4444',
      colorInfo: isDark ? '#00d4ff' : '#3b82f6',
      borderRadius: 8,
      fontSize: 14,
      fontFamily: 'var(--font-family)',
      // Dark mode specific tokens
      ...(isDark && {
        colorBgContainer: 'var(--color-surface)',
        colorBgElevated: 'var(--color-surface)',
        colorBgLayout: 'var(--color-background)',
        colorBorder: 'var(--color-border)',
        colorBorderSecondary: 'var(--color-border)',
        colorText: 'var(--color-text)',
        colorTextSecondary: 'var(--color-text-secondary)',
        colorTextTertiary: 'var(--color-text-muted)',
        colorTextQuaternary: 'var(--color-text-muted)',
        colorFill: 'var(--color-surface-hover)',
        colorFillSecondary: 'var(--color-surface-active)',
        colorFillTertiary: 'var(--color-surface-active)',
        colorFillQuaternary: 'var(--color-surface-active)',
      }),
    },
    components: {
      Layout: {
        headerBg: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        headerPadding: "0 24px",
        bodyBg: 'var(--color-background)',
        siderBg: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
      },
      Table: {
        headerBg: isDark ? 'var(--color-surface-hover)' : 'var(--color-surface-hover)',
        headerColor: isDark ? 'var(--color-text)' : 'var(--color-text)',
        rowHoverBg: isDark ? 'var(--color-surface-active)' : 'var(--color-surface-active)',
        borderColor: 'var(--color-border)',
        headerSplitColor: 'var(--color-border)',
      },
      Card: {
        headerBg: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        headerColor: isDark ? 'var(--color-text)' : 'var(--color-text)',
        colorBgContainer: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        colorBorderSecondary: 'var(--color-border)',
      },
      Button: {
        borderRadius: 8,
        controlHeight: 36,
        primaryShadow: 'none',
      },
      Input: {
        borderRadius: 8,
        colorBgContainer: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        colorBorder: 'var(--color-border)',
        colorText: isDark ? 'var(--color-text)' : 'var(--color-text)',
        colorTextPlaceholder: isDark ? 'var(--color-text-muted)' : 'var(--color-text-muted)',
      },
      Select: {
        borderRadius: 8,
        colorBgContainer: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        colorBorder: 'var(--color-border)',
        colorText: isDark ? 'var(--color-text)' : 'var(--color-text)',
        colorTextPlaceholder: isDark ? 'var(--color-text-muted)' : 'var(--color-text-muted)',
      },
      Alert: {
        borderRadius: 8,
        colorBgContainer: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        colorBorder: 'var(--color-border)',
      },
      Tag: {
        borderRadius: 6,
      },
      Tooltip: {
        colorBgSpotlight: isDark ? 'var(--color-surface)' : 'var(--color-surface)',
        colorTextLightSolid: isDark ? 'var(--color-text)' : 'var(--color-text)',
      },
    },
  };

  return (
    <ConfigProvider theme={antTheme}>
      <AntApp>
        {children}
      </AntApp>
    </ConfigProvider>
  );
};

function App() {
  console.log("🚀 App component initializing...");
  console.log("🔧 App environment:", {
    NODE_ENV: process.env.NODE_ENV,
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    VITE_BACKEND_PORT: import.meta.env.VITE_BACKEND_PORT,
    VITE_FRONTEND_PORT: import.meta.env.VITE_FRONTEND_PORT,
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AntDesignTheme>
          <div className="min-h-screen bg-theme font-theme">
            <Dashboard />
          </div>
        </AntDesignTheme>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
