import React from 'react';
import { Card, Statistic, Row, Col, Spin, Alert } from 'antd';
import {
  DatabaseOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { useDashboardSummary } from '../hooks/useTraces';
import { formatters } from '../utils/formatters';

const DashboardStats: React.FC = () => {
  const { data: summary, isLoading, error } = useDashboardSummary();

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert
        message="Failed to load dashboard statistics"
        description={error.message}
        type="error"
        showIcon
      />
    );
  }

  if (!summary) {
    return null;
  }

  const { stats } = summary;

  // Calculate status percentages
  const totalWithStatus = Object.values(stats.status_distribution).reduce((a, b) => a + b, 0);
  const completedCount = stats.status_distribution.completed || 0;
  const failedCount = stats.status_distribution.failed || 0;
  const runningCount = stats.status_distribution.running || 0;

  const successRate = totalWithStatus > 0 ? ((completedCount / totalWithStatus) * 100).toFixed(1) : '0';

  return (
    <div className="space-y-4">
      {/* Main Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Traces"
              value={stats.total_traces}
              prefix={<BranchesOutlined className="text-blue-500" />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Runs"
              value={stats.total_runs}
              prefix={<DatabaseOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Recent (24h)"
              value={stats.recent_runs_24h}
              prefix={<ClockCircleOutlined className="text-orange-500" />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={successRate}
              suffix="%"
              prefix={<CheckCircleOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Detailed Statistics */}
      <Row gutter={[16, 16]}>
        {/* Status Distribution */}
        <Col xs={24} lg={8}>
          <Card title="Status Distribution" size="small">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="flex items-center">
                  <CheckCircleOutlined className="text-green-500 mr-2" />
                  Completed
                </span>
                <span className="font-semibold">{formatters.formatNumber(completedCount)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center">
                  <LoadingOutlined className="text-blue-500 mr-2" />
                  Running
                </span>
                <span className="font-semibold">{formatters.formatNumber(runningCount)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center">
                  <ExclamationCircleOutlined className="text-red-500 mr-2" />
                  Failed
                </span>
                <span className="font-semibold">{formatters.formatNumber(failedCount)}</span>
              </div>
            </div>
          </Card>
        </Col>

        {/* Run Type Distribution */}
        <Col xs={24} lg={8}>
          <Card title="Run Types" size="small">
            <div className="space-y-2">
              {Object.entries(stats.run_type_distribution).map(([type, count]) => {
                const { text, icon } = formatters.formatRunType(type);
                return (
                  <div key={type} className="flex justify-between items-center">
                    <span className="flex items-center">
                      <span className="mr-2">{icon}</span>
                      {text}
                    </span>
                    <span className="font-semibold">{formatters.formatNumber(count)}</span>
                  </div>
                );
              })}
            </div>
          </Card>
        </Col>

        {/* Project Distribution */}
        <Col xs={24} lg={8}>
          <Card title="Projects" size="small">
            <div className="space-y-2">
              {Object.entries(stats.project_distribution).length > 0 ? (
                Object.entries(stats.project_distribution)
                  .sort(([, a], [, b]) => b - a) // Sort by count descending
                  .slice(0, 5) // Show top 5 projects
                  .map(([project, count]) => (
                    <div key={project} className="flex justify-between items-center">
                      <span className="truncate mr-2" title={project}>
                        {formatters.truncateString(project, 20)}
                      </span>
                      <span className="font-semibold">{formatters.formatNumber(count)}</span>
                    </div>
                  ))
              ) : (
                <div className="text-gray-500 text-sm">No projects found</div>
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardStats;
