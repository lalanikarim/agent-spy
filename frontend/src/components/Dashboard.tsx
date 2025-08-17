import { ApiOutlined, DashboardOutlined } from "@ant-design/icons";
import { Alert, Layout, Spin, Typography } from "antd";
import React, { useCallback, useEffect, useState } from "react";
import { getBaseUrl } from "../config/environment";
import { useHealth, useTraceHierarchy } from "../hooks/useTraces";
import { useWebSocket } from "../hooks/useWebSocket";
import ConnectionStatus from "./ConnectionStatus";
import DashboardStats from "./DashboardStats";
import RealTimeNotifications from "./RealTimeNotifications";
import ThemeToggle from "./ThemeToggle";
import TraceDetail from "./TraceDetail";
import TraceTable from "./TraceTable";
import Card from "./ui/Card";

const { Header, Content } = Layout;
const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [isDetailExpanded, setIsDetailExpanded] = useState<boolean>(false);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [realtimeEnabled, setRealtimeEnabled] = useState<boolean>(true);

  // Health check to ensure backend is available
  const { isLoading: healthLoading, error: healthError } = useHealth();

  // WebSocket connection for real-time updates
  const {
    isConnected: wsConnected,
    connectionError: wsError,
    subscribedEvents,
    subscribe,
    unsubscribe,
  } = useWebSocket();

  // Get hierarchy loading state for refresh button
  const { isLoading: hierarchyLoading } = useTraceHierarchy(selectedTraceId, {
    enabled: !healthError && !!selectedTraceId,
  });

  const handleTraceSelect = (traceId: string) => {
    setSelectedTraceId(traceId);
  };

  const handleTraceDeselect = () => {
    setSelectedTraceId(null);
    setIsDetailExpanded(false); // Reset expansion when closing detail
  };

  const handleToggleExpansion = () => {
    setIsDetailExpanded(!isDetailExpanded);
  };

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

  // Handle real-time toggle
  const handleToggleRealtime = useCallback((enabled: boolean) => {
    setRealtimeEnabled(enabled);
  }, []);

  // Coordinated refresh for both root traces and trace detail
  const handleRefresh = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  // Separate refresh for trace hierarchy only
  const handleHierarchyRefresh = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  return (
    <Layout className="min-h-screen">
      {/* Real-time Notifications */}
      <RealTimeNotifications
        isConnected={wsConnected}
        subscribedEvents={subscribedEvents}
      />

      {/* Header */}
      <Header className="bg-surface border-b border-gray-100 shadow-theme-sm backdrop-blur-theme">
        <div className="flex items-center justify-between px-6 py-0 h-16">
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

          {/* Health Status, WebSocket Connection, and Theme Toggle */}
          <div className="flex items-center space-x-3">
            {/* Backend Health Status */}
            <div className="flex items-center px-3 py-2 bg-surface-hover rounded-theme-lg border border-gray-100">
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
        <div className="max-w-7xl mx-auto">
          {/* Backend Connection Error */}
          {healthError && (
            <div className="mb-8">
              <Alert
                message="Backend Connection Error"
                description={`Cannot connect to Agent Spy backend. Please ensure the server is running at ${getBaseUrl()}`}
                type="error"
                showIcon
                className="rounded-theme-lg border border-error"
              />
            </div>
          )}

          {/* Dashboard Statistics */}
          <div className="mb-8">
            <DashboardStats />
          </div>

          {/* Main Dashboard Content */}
          <div className="flex gap-8">
            {/* Master Table - Root Traces */}
            {!isDetailExpanded && (
              <div className={selectedTraceId ? "flex-1 min-w-0" : "w-full"}>
                <Card className="h-full shadow-2xl">
                  <TraceTable
                    selectedTraceId={selectedTraceId}
                    onTraceSelect={handleTraceSelect}
                    onRefresh={handleRefresh}
                    refreshTrigger={refreshTrigger}
                    disabled={!!healthError}
                  />
                </Card>
              </div>
            )}

            {/* Detail View - Trace Hierarchy (only show when trace selected) */}
            {selectedTraceId && (
              <div
                className={isDetailExpanded ? "w-full" : "w-120 flex-shrink-0"}
                style={
                  !isDetailExpanded
                    ? { width: "480px", minWidth: "480px", maxWidth: "480px" }
                    : {}
                }
              >
                <TraceDetail
                  traceId={selectedTraceId}
                  onClose={handleTraceDeselect}
                  onToggleExpansion={handleToggleExpansion}
                  isExpanded={isDetailExpanded}
                  refreshTrigger={refreshTrigger}
                  onRefresh={handleHierarchyRefresh}
                  refreshLoading={hierarchyLoading}
                  disabled={!!healthError}
                />
              </div>
            )}
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default Dashboard;
