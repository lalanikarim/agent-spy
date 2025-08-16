import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App as AntApp, ConfigProvider } from "antd";
import "./App.css";
import Dashboard from "./components/Dashboard";

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

// Ant Design theme configuration
const theme = {
  token: {
    colorPrimary: "#1890ff",
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      headerBg: "#ffffff",
      headerPadding: "0 24px",
    },
    Table: {
      headerBg: "#fafafa",
    },
  },
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
      <ConfigProvider theme={theme}>
        <AntApp>
          <div className="min-h-screen bg-gray-50">
            <Dashboard />
          </div>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
