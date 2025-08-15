import React, { useState } from 'react';
import { Layout, Typography, Alert, Spin } from 'antd';
import { DashboardOutlined, ApiOutlined } from '@ant-design/icons';
import TraceTable from './TraceTable';
import TraceDetail from './TraceDetail';
import DashboardStats from './DashboardStats';
import { useHealth } from '../hooks/useTraces';

const { Header, Content } = Layout;
const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  
  // Health check to ensure backend is available
  const { isLoading: healthLoading, error: healthError } = useHealth();

  const handleTraceSelect = (traceId: string) => {
    setSelectedTraceId(traceId);
  };

  const handleTraceDeselect = () => {
    setSelectedTraceId(null);
  };

  return (
    <Layout className="min-h-screen">
      {/* Header */}
      <Header className="bg-white shadow-sm border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DashboardOutlined className="text-xl text-blue-600" />
            <Title level={3} className="m-0 text-gray-800">
              Agent Spy Dashboard
            </Title>
          </div>
          
          {/* Health Status Indicator */}
          <div className="flex items-center space-x-2">
            {healthLoading ? (
              <Spin size="small" />
            ) : healthError ? (
              <div className="flex items-center space-x-2 text-red-500">
                <ApiOutlined />
                <span className="text-sm">Backend Offline</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-green-500">
                <ApiOutlined />
                <span className="text-sm">Backend Online</span>
              </div>
            )}
          </div>
        </div>
      </Header>

      {/* Main Content */}
      <Content className="p-6">
        {/* Backend Connection Error */}
        {healthError && (
          <Alert
            message="Backend Connection Error"
            description="Cannot connect to Agent Spy backend. Please ensure the server is running at http://localhost:8000"
            type="error"
            showIcon
            className="mb-6"
          />
        )}

        {/* Dashboard Statistics */}
        <div className="mb-6">
          <DashboardStats />
        </div>

        {/* Main Dashboard Content */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Master Table - Root Traces */}
          <div className="xl:col-span-2">
            <TraceTable
              selectedTraceId={selectedTraceId}
              onTraceSelect={handleTraceSelect}
              disabled={!!healthError}
            />
          </div>

          {/* Detail View - Trace Hierarchy */}
          <div className="xl:col-span-1">
            <TraceDetail
              traceId={selectedTraceId}
              onClose={handleTraceDeselect}
              disabled={!!healthError}
            />
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default Dashboard;
