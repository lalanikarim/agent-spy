import React from 'react';
import { Card, Statistic, Row, Col, Spin, Alert } from 'antd';
import {
  DatabaseOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FastForwardOutlined,
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
    <div className="space-y-6">
      {/* Main Statistics */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6 hover:shadow-theme-xl transition-all duration-theme-normal group">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-theme-lg group-hover:bg-primary/20 transition-colors duration-theme-normal">
                <BranchesOutlined className="text-xl text-primary" />
              </div>
              <div className="text-text-secondary text-theme-sm font-theme-medium">
                Total Traces
              </div>
            </div>
            <div className="text-theme-3xl font-theme-bold text-text mb-2">
              {formatters.formatNumber(stats.total_traces)}
            </div>
            <div className="text-text-secondary text-theme-sm">
              All time traces
            </div>
          </div>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6 hover:shadow-theme-xl transition-all duration-theme-normal group">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center justify-center w-12 h-12 bg-success/10 rounded-theme-lg group-hover:bg-success/20 transition-colors duration-theme-normal">
                <DatabaseOutlined className="text-xl text-success" />
              </div>
              <div className="text-text-secondary text-theme-sm font-theme-medium">
                Total Runs
              </div>
            </div>
            <div className="text-theme-3xl font-theme-bold text-text mb-2">
              {formatters.formatNumber(stats.total_runs)}
            </div>
            <div className="text-text-secondary text-theme-sm">
              All time executions
            </div>
          </div>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6 hover:shadow-theme-xl transition-all duration-theme-normal group">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center justify-center w-12 h-12 bg-warning/10 rounded-theme-lg group-hover:bg-warning/20 transition-colors duration-theme-normal">
                <ClockCircleOutlined className="text-xl text-warning" />
              </div>
              <div className="text-text-secondary text-theme-sm font-theme-medium">
                Recent (24h)
              </div>
            </div>
            <div className="text-theme-3xl font-theme-bold text-text mb-2">
              {formatters.formatNumber(stats.recent_runs_24h)}
            </div>
            <div className="text-text-secondary text-theme-sm">
              Last 24 hours
            </div>
          </div>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6 hover:shadow-theme-xl transition-all duration-theme-normal group">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center justify-center w-12 h-12 bg-success/10 rounded-theme-lg group-hover:bg-success/20 transition-colors duration-theme-normal">
                <CheckCircleOutlined className="text-xl text-success" />
              </div>
              <div className="text-text-secondary text-theme-sm font-theme-medium">
                Success Rate
              </div>
            </div>
            <div className="text-theme-3xl font-theme-bold text-text mb-2">
              {successRate}%
            </div>
            <div className="text-text-secondary text-theme-sm">
              Completion rate
            </div>
          </div>
        </Col>
      </Row>

      {/* Detailed Statistics */}
      <Row gutter={[24, 24]}>
        {/* Status Distribution */}
        <Col xs={24} lg={8}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6">
            <div className="flex items-center mb-4">
              <div className="flex items-center justify-center w-8 h-8 bg-primary/10 rounded-theme-md mr-3">
                <BranchesOutlined className="text-primary" />
              </div>
              <h3 className="text-theme-lg font-theme-semibold text-text m-0">Status Distribution</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-surface-hover rounded-theme-md">
                <span className="flex items-center text-text">
                  <CheckCircleOutlined className="text-success mr-3 text-lg" />
                  <span className="font-theme-medium">Completed</span>
                </span>
                <span className="font-theme-bold text-theme-lg text-text">{formatters.formatNumber(completedCount)}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-surface-hover rounded-theme-md">
                <span className="flex items-center text-text">
                  <FastForwardOutlined className="text-primary mr-3 text-lg" />
                  <span className="font-theme-medium">Running</span>
                </span>
                <span className="font-theme-bold text-theme-lg text-text">{formatters.formatNumber(runningCount)}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-surface-hover rounded-theme-md">
                <span className="flex items-center text-text">
                  <ExclamationCircleOutlined className="text-error mr-3 text-lg" />
                  <span className="font-theme-medium">Failed</span>
                </span>
                <span className="font-theme-bold text-theme-lg text-text">{formatters.formatNumber(failedCount)}</span>
              </div>
            </div>
          </div>
        </Col>

        {/* Run Type Distribution */}
        <Col xs={24} lg={8}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6">
            <div className="flex items-center mb-4">
              <div className="flex items-center justify-center w-8 h-8 bg-secondary/10 rounded-theme-md mr-3">
                <DatabaseOutlined className="text-secondary" />
              </div>
              <h3 className="text-theme-lg font-theme-semibold text-text m-0">Run Types</h3>
            </div>
            <div className="space-y-4">
              {Object.entries(stats.run_type_distribution).map(([type, count]) => {
                const { text, icon } = formatters.formatRunType(type);
                return (
                  <div key={type} className="flex justify-between items-center p-3 bg-surface-hover rounded-theme-md">
                    <span className="flex items-center text-text">
                      <span className="mr-3 text-lg">{icon}</span>
                      <span className="font-theme-medium">{text}</span>
                    </span>
                    <span className="font-theme-bold text-theme-lg text-text">{formatters.formatNumber(count)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </Col>

        {/* Project Distribution */}
        <Col xs={24} lg={8}>
          <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-border p-6">
            <div className="flex items-center mb-4">
              <div className="flex items-center justify-center w-8 h-8 bg-warning/10 rounded-theme-md mr-3">
                <ClockCircleOutlined className="text-warning" />
              </div>
              <h3 className="text-theme-lg font-theme-semibold text-text m-0">Top Projects</h3>
            </div>
            <div className="space-y-4">
              {Object.entries(stats.project_distribution).length > 0 ? (
                Object.entries(stats.project_distribution)
                  .sort(([, a], [, b]) => b - a) // Sort by count descending
                  .slice(0, 5) // Show top 5 projects
                  .map(([project, count]) => (
                    <div key={project} className="flex justify-between items-center p-3 bg-surface-hover rounded-theme-md">
                      <span className="truncate mr-2 text-text font-theme-medium" title={project}>
                        {formatters.truncateString(project, 20)}
                      </span>
                      <span className="font-theme-bold text-theme-lg text-text">{formatters.formatNumber(count)}</span>
                    </div>
                  ))
              ) : (
                <div className="text-text-muted text-theme-sm p-3 bg-surface-hover rounded-theme-md">No projects found</div>
              )}
            </div>
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardStats;
