import {
  BranchesOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  ExclamationCircleOutlined,
  FastForwardOutlined,
} from "@ant-design/icons";
import { Alert, Card, Col, Row, Spin } from "antd";
import React from "react";
import { useDashboardSummary } from "../hooks/useTraces";
import { formatters } from "../utils/formatters";
import StatCard from "./ui/StatCard";
import StatusCard from "./ui/StatusCard";

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
  const totalWithStatus = Object.values(stats.status_distribution).reduce(
    (a, b) => a + b,
    0
  );
  const completedCount = stats.status_distribution.completed || 0;
  const failedCount = stats.status_distribution.failed || 0;
  const runningCount = stats.status_distribution.running || 0;

  const successRate =
    totalWithStatus > 0
      ? ((completedCount / totalWithStatus) * 100).toFixed(1)
      : "0";

  return (
    <div className="space-y-6">
      {/* Main Statistics */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Total Traces"
            value={formatters.formatNumber(stats.total_traces)}
            icon={<BranchesOutlined />}
            iconBgColor="bg-blue-100"
            iconColor="text-blue-600"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Total Runs"
            value={formatters.formatNumber(stats.total_runs)}
            icon={<DatabaseOutlined />}
            iconBgColor="bg-green-100"
            iconColor="text-green-600"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Recent (24h)"
            value={formatters.formatNumber(stats.recent_runs_24h)}
            icon={<ClockCircleOutlined />}
            iconBgColor="bg-orange-100"
            iconColor="text-orange-600"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Success Rate"
            value={`${successRate}%`}
            icon={<CheckCircleOutlined />}
            iconBgColor="bg-green-100"
            iconColor="text-green-600"
          />
        </Col>
      </Row>

      {/* Detailed Statistics */}
      <Row gutter={[24, 24]}>
        {/* Status Distribution */}
        <Col xs={24} lg={8}>
          <StatusCard
            title="Status Distribution"
            description="Trace status overview"
            headerIcon={<BranchesOutlined />}
            headerIconBgColor="bg-blue-100"
            headerIconColor="text-blue-600"
            items={[
              {
                icon: <CheckCircleOutlined />,
                title: "Completed",
                count: completedCount,
                iconBgColor: "bg-green-100",
                iconColor: "text-green-600",
              },
              {
                icon: <FastForwardOutlined />,
                title: "Running",
                count: runningCount,
                iconBgColor: "bg-blue-100",
                iconColor: "text-blue-600",
              },
              {
                icon: <ExclamationCircleOutlined />,
                title: "Failed",
                count: failedCount,
                iconBgColor: "bg-red-100",
                iconColor: "text-red-600",
              },
            ]}
          />
        </Col>

        {/* Run Type Distribution */}
        <Col xs={24} lg={8}>
          <StatusCard
            title="Run Types"
            description="Execution type breakdown"
            headerIcon={<DatabaseOutlined />}
            headerIconBgColor="bg-indigo-100"
            headerIconColor="text-indigo-600"
            items={Object.entries(stats.run_type_distribution).map(
              ([type, count]) => {
                const { text, icon } = formatters.formatRunType(type);
                return {
                  icon: icon,
                  title: text,
                  count: count,
                  iconBgColor: "bg-indigo-100",
                  iconColor: "text-indigo-600",
                };
              }
            )}
          />
        </Col>

        {/* Project Distribution */}
        <Col xs={24} lg={8}>
          <StatusCard
            title="Top Projects"
            description="Most active projects"
            headerIcon={<ClockCircleOutlined />}
            headerIconBgColor="bg-orange-100"
            headerIconColor="text-orange-600"
            items={
              Object.entries(stats.project_distribution).length > 0
                ? Object.entries(stats.project_distribution)
                    .sort(([, a], [, b]) => b - a) // Sort by count descending
                    .slice(0, 5) // Show top 5 projects
                    .map(([project, count]) => ({
                      icon: "📁",
                      title: formatters.truncateString(project, 20),
                      count: count,
                      iconBgColor: "bg-orange-100",
                      iconColor: "text-orange-600",
                    }))
                : []
            }
          />
        </Col>
      </Row>
    </div>
  );
};

export default DashboardStats;
