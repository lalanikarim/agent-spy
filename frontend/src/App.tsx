import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App as AntApp, ConfigProvider } from "antd";
import "./App.css";
import Dashboard from "./components/Dashboard";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import "./styles/theme.css";

// App module loaded

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
const AntDesignTheme: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { theme } = useTheme();

  const isDark = theme === "dark";

  const antTheme = {
    token: {
      colorPrimary: isDark ? "#00d4ff" : "#3b82f6",
      colorSuccess: "#10b981",
      colorWarning: "#f59e0b",
      colorError: "#ef4444",
      colorInfo: isDark ? "#00d4ff" : "#3b82f6",
      borderRadius: 8,
      fontSize: 14,
      fontFamily: "var(--font-family)",
      // Dark mode specific tokens
      ...(isDark && {
        colorBgContainer: "var(--color-surface)",
        colorBgElevated: "var(--color-surface)",
        colorBgLayout: "var(--color-background)",
        colorBorder: "var(--color-border)",
        colorBorderSecondary: "var(--color-border)",
        colorText: "var(--color-text)",
        colorTextSecondary: "var(--color-text-secondary)",
        colorTextTertiary: "var(--color-text-muted)",
        colorTextQuaternary: "var(--color-text-muted)",
        colorFill: "var(--color-surface-hover)",
        colorFillSecondary: "var(--color-surface-active)",
        colorFillTertiary: "var(--color-surface-active)",
        colorFillQuaternary: "var(--color-surface-active)",
      }),
    },
    components: {
      Layout: {
        headerBg: isDark ? "var(--color-surface)" : "var(--color-surface)",
        headerPadding: "0 24px",
        bodyBg: "var(--color-background)",
        siderBg: isDark ? "var(--color-surface)" : "var(--color-surface)",
      },
      Table: {
        headerBg: isDark
          ? "var(--color-surface-hover)"
          : "var(--color-surface-hover)",
        headerColor: isDark ? "var(--color-text)" : "var(--color-text)",
        rowHoverBg: isDark
          ? "var(--color-surface-active)"
          : "var(--color-surface-active)",
        borderColor: "var(--color-border)",
        headerSplitColor: "var(--color-border)",
        colorBgContainer: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorText: isDark ? "var(--color-text)" : "var(--color-text)",
        colorTextHeading: isDark ? "var(--color-text)" : "var(--color-text)",
        colorFillAlter: isDark
          ? "var(--color-surface-hover)"
          : "var(--color-surface-hover)",
      },
      Card: {
        headerBg: isDark ? "var(--color-surface)" : "var(--color-surface)",
        headerColor: isDark ? "var(--color-text)" : "var(--color-text)",
        colorBgContainer: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorBorderSecondary: "var(--color-border)",
      },
      Button: {
        borderRadius: 8,
        controlHeight: 36,
        primaryShadow: isDark ? "none" : "0 2px 0 rgba(0, 0, 0, 0.045)",
        colorBgContainer: isDark ? "#1e293b" : "#ffffff",
        colorBorder: isDark ? "#334155" : "#e2e8f0",
        colorText: isDark ? "#e2e8f0" : "#1e293b",
        colorPrimary: isDark ? "#00d4ff" : "#3b82f6",
        colorPrimaryHover: isDark ? "#00b8e6" : "#2563eb",
        colorPrimaryActive: isDark ? "#0099cc" : "#1d4ed8",
        borderWidth: isDark ? 1 : 1,
      },
      Input: {
        borderRadius: 8,
        colorBgContainer: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorBorder: "var(--color-border)",
        colorText: isDark ? "var(--color-text)" : "var(--color-text)",
        colorTextPlaceholder: isDark
          ? "var(--color-text-muted)"
          : "var(--color-text-muted)",
      },
      Select: {
        borderRadius: 8,
        colorBgContainer: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorBorder: "var(--color-border)",
        colorText: isDark ? "var(--color-text)" : "var(--color-text)",
        colorTextPlaceholder: isDark
          ? "var(--color-text-muted)"
          : "var(--color-text-muted)",
        colorBgElevated: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorTextQuaternary: isDark
          ? "var(--color-text-muted)"
          : "var(--color-text-muted)",
      },
      Alert: {
        borderRadius: 8,
        colorBgContainer: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorBorder: "var(--color-border)",
      },
      Tag: {
        borderRadius: 6,
      },
      Tooltip: {
        colorBgSpotlight: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorTextLightSolid: isDark ? "var(--color-text)" : "var(--color-text)",
      },
      Tree: {
        colorBgContainer: isDark
          ? "var(--color-surface)"
          : "var(--color-surface)",
        colorText: isDark ? "var(--color-text)" : "var(--color-text)",
        colorBorder: "var(--color-border)",
        colorFill: isDark
          ? "var(--color-surface-hover)"
          : "var(--color-surface-hover)",
        colorFillSecondary: isDark
          ? "var(--color-surface-active)"
          : "var(--color-surface-active)",
      },
    },
  };

  return (
    <ConfigProvider theme={antTheme}>
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  );
};

function App() {
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
