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
  const [isDetailExpanded, setIsDetailExpanded] = useState<boolean>(false);
  
  // Health check to ensure backend is available
  const { isLoading: healthLoading, error: healthError } = useHealth();

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
        <div className="flex gap-6 overflow-hidden">
          {/* Master Table - Root Traces */}
          {!isDetailExpanded && (
            <div className={selectedTraceId ? 'flex-1 min-w-0 overflow-hidden' : 'w-full'}>
              <TraceTable
                selectedTraceId={selectedTraceId}
                onTraceSelect={handleTraceSelect}
                disabled={!!healthError}
              />
            </div>
          )}

          {/* Detail View - Trace Hierarchy (only show when trace selected) */}
          {selectedTraceId && (
            <div 
              className={isDetailExpanded ? 'w-full overflow-hidden' : 'w-120 flex-shrink-0 overflow-hidden'}
              style={!isDetailExpanded ? { width: '480px', minWidth: '480px', maxWidth: '480px' } : {}}
            >
              <TraceDetail
                traceId={selectedTraceId}
                onClose={handleTraceDeselect}
                onToggleExpansion={handleToggleExpansion}
                isExpanded={isDetailExpanded}
                disabled={!!healthError}
              />
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default Dashboard;
