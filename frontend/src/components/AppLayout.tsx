import { ApiOutlined, DashboardOutlined } from "@ant-design/icons";
import { Layout, Menu, Spin, Typography } from "antd";
import React, { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useHealth } from "../hooks/useTraces";
import { useWebSocket } from "../hooks/useWebSocket";
import ConnectionStatus from "./ConnectionStatus";
import RealTimeNotifications from "./RealTimeNotifications";
import ThemeToggle from "./ThemeToggle";

const { Header, Content } = Layout;
const { Title } = Typography;

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [realtimeEnabled, setRealtimeEnabled] = useState<boolean>(true);
  const location = useLocation();
  const navigate = useNavigate();

  // Health check
  const { isLoading: healthLoading, error: healthError } = useHealth();

  // WebSocket connection for real-time updates
  const {
    isConnected: wsConnected,
    connectionError: wsError,
    subscribedEvents,
    subscribe,
    unsubscribe,
  } = useWebSocket();

  // Subscribe to WebSocket events when connected
  useEffect(() => {
    if (wsConnected && realtimeEnabled) {
      subscribe([
        "trace.created",
        "trace.updated",
        "trace.completed",
        "trace.failed",
        "stats.updated",
      ]);
    } else if (wsConnected && !realtimeEnabled) {
      unsubscribe([
        "trace.created",
        "trace.updated",
        "trace.completed",
        "trace.failed",
        "stats.updated",
      ]);
    }
  }, [wsConnected, realtimeEnabled, subscribe, unsubscribe]);

  const handleToggleRealtime = useCallback((enabled: boolean) => {
    setRealtimeEnabled(enabled);
  }, []);

  // Active menu key based on path
  const selectedKeys = React.useMemo(() => {
    if (location.pathname.startsWith("/traces")) return ["traces"];
    return ["home"];
  }, [location.pathname]);

  const onMenuClick = (key: string) => {
    if (key === "home") navigate("/");
    if (key === "traces") navigate("/traces");
  };

  return (
    <Layout className="min-h-screen">
      {/* Real-time Notifications */}
      <RealTimeNotifications
        isConnected={wsConnected}
        subscribedEvents={subscribedEvents}
      />

      {/* Header */}
      <Header className="bg-surface border-b border-gray-100 dark:border-gray-700 shadow-theme-sm backdrop-blur-theme">
        <div className="flex items-center justify-between px-6 py-0 h-16 gap-4">
          {/* Brand */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center justify-center w-10 h-10 bg-primary rounded-theme-lg shadow-theme-sm">
              <DashboardOutlined className="text-xl text-text-inverse" />
            </div>
            <div className="flex flex-col justify-center">
              <Title
                level={3}
                className="m-0 text-text font-theme-bold leading-tight"
              >
                Agent Spy Dashboard
              </Title>
              <div className="text-text-secondary text-theme-sm font-theme-medium leading-tight">
                Real-time monitoring & analytics
              </div>
            </div>
          </div>

          {/* Center Navigation */}
          <div className="flex-1 flex justify-center">
            <Menu
              mode="horizontal"
              selectedKeys={selectedKeys}
              onClick={(info) => onMenuClick(info.key as string)}
              items={[
                { key: "home", label: <Link to="/">Home</Link> },
                { key: "traces", label: <Link to="/traces">Traces</Link> },
              ]}
              disabledOverflow
            />
          </div>

          {/* Health Status, WebSocket Connection, and Theme Toggle */}
          <div className="flex items-center space-x-3">
            {/* Backend Health Status */}
            <div className="flex items-center px-3 py-2 bg-surface-hover rounded-theme-lg border border-gray-100 dark:border-gray-700">
              {healthLoading ? (
                <div className="flex items-center space-x-2">
                  <Spin size="small" />
                  <span className="text-sm text-text-secondary">
                    Checking...
                  </span>
                </div>
              ) : healthError ? (
                <div className="flex items-center space-x-2 text-error">
                  <ApiOutlined className="text-base" />
                  <span className="text-sm font-theme-medium">
                    Backend Offline
                  </span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-success">
                  <ApiOutlined className="text-base" />
                  <span className="text-sm font-theme-medium">
                    Backend Online
                  </span>
                </div>
              )}
            </div>

            {/* WebSocket Connection Status */}
            <ConnectionStatus
              isConnected={wsConnected}
              connectionError={wsError}
              subscribedEvents={subscribedEvents}
              onToggleRealtime={handleToggleRealtime}
              realtimeEnabled={realtimeEnabled}
            />

            {/* Theme Toggle */}
            <ThemeToggle size="middle" />
          </div>
        </div>
      </Header>

      {/* Main Content */}
      <Content className="px-12 py-8 bg-theme">
        <div className="max-w-7xl mx-auto">{children}</div>
      </Content>
    </Layout>
  );
};

export default AppLayout;
