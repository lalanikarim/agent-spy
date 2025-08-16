import {
  ClearOutlined,
  FilterOutlined,
  ReloadOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Col,
  Input,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import type { ColumnsType, TableProps } from "antd/es/table";
import React, { useMemo, useState } from "react";
import { useRootTraces } from "../hooks/useTraces";
import type { PaginationParams, TraceFilters, TraceRun } from "../types/traces";
import { formatters } from "../utils/formatters";

const { Text } = Typography;
const { Option } = Select;

interface TraceTableProps {
  selectedTraceId: string | null;
  onTraceSelect: (traceId: string) => void;
  onRefresh: () => void;
  refreshTrigger: number;
  disabled?: boolean;
}

const TraceTable: React.FC<TraceTableProps> = ({
  selectedTraceId,
  onTraceSelect,
  onRefresh,
  refreshTrigger,
  disabled = false,
}) => {
  // State for filters and pagination
  const [filters, setFilters] = useState<TraceFilters>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    limit: 50,
    offset: 0,
  });
  const [searchText, setSearchText] = useState("");

  // Fetch root traces
  const { data, isLoading, error, refetch } = useRootTraces(
    filters,
    pagination,
    { enabled: !disabled }
  );

  // Trigger refetch when refreshTrigger changes
  React.useEffect(() => {
    if (refreshTrigger > 0) {
      refetch();
    }
  }, [refreshTrigger, refetch]);

  // Handle filter changes
  const handleFilterChange = (
    key: keyof TraceFilters,
    value: string | undefined
  ) => {
    const newFilters = { ...filters };
    if (value) {
      newFilters[key] = value;
    } else {
      delete newFilters[key];
    }
    setFilters(newFilters);
    setPagination({ ...pagination, offset: 0 }); // Reset to first page
  };

  // Handle search
  const handleSearch = () => {
    handleFilterChange("search", searchText || undefined);
  };

  // Handle clear filters
  const handleClearFilters = () => {
    setFilters({});
    setSearchText("");
    setPagination({ limit: 50, offset: 0 });
  };

  // Handle table pagination
  const handleTableChange: TableProps<TraceRun>["onChange"] = (
    paginationInfo
  ) => {
    const newOffset =
      ((paginationInfo.current || 1) - 1) * (paginationInfo.pageSize || 50);
    setPagination({
      limit: paginationInfo.pageSize || 50,
      offset: newOffset,
    });
  };

  // Table columns
  const columns: ColumnsType<TraceRun> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      width: 250,
      render: (name: string, record: TraceRun) => (
        <div>
          <Text strong className="block">
            {formatters.truncateString(name, 30)}
          </Text>
          <Text type="secondary" className="text-xs">
            {record.id.slice(0, 8)}...
          </Text>
        </div>
      ),
    },
    {
      title: "Type",
      dataIndex: "run_type",
      key: "run_type",
      width: 100,
      render: (runType: string) => {
        const { text, icon } = formatters.formatRunType(runType);
        return (
          <Tooltip title={`Run Type: ${text}`}>
            <Tag className="flex items-center">
              <span className="mr-1">{icon}</span>
              {text}
            </Tag>
          </Tooltip>
        );
      },
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status: string) => {
        const { text, color } = formatters.formatStatus(status);
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: "Duration",
      dataIndex: "duration_ms",
      key: "duration_ms",
      width: 100,
      render: (duration: number | null, record: TraceRun) => {
        return (
          <Text className="font-mono text-sm">
            {formatters.formatTaskDuration(
              duration,
              record.start_time,
              record.end_time || null,
              record.status
            )}
          </Text>
        );
      },
    },
    {
      title: "Started",
      dataIndex: "start_time",
      key: "start_time",
      width: 150,
      render: (startTime: string) => (
        <Tooltip title={formatters.formatDateTime(startTime)}>
          <Text className="text-sm">
            {formatters.formatRelativeTime(startTime)}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: "Project",
      dataIndex: "project_name",
      key: "project_name",
      width: 120,
      render: (project: string | null) =>
        project ? (
          <Tag color="blue">{formatters.truncateString(project, 15)}</Tag>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
  ];

  // Row selection
  const rowSelection = {
    type: "radio" as const,
    selectedRowKeys: selectedTraceId ? [selectedTraceId] : [],
    onSelect: (record: TraceRun) => {
      onTraceSelect(record.id);
    },
  };

  // Get unique values for filter dropdowns
  const uniqueProjects = useMemo(() => {
    if (!data?.runs) return [];
    const projects = data.runs
      .map((run) => run.project_name)
      .filter((project): project is string => !!project);
    return [...new Set(projects)];
  }, [data?.runs]);

  const uniqueStatuses = useMemo(() => {
    if (!data?.runs) return [];
    const statuses = data.runs.map((run) => run.status);
    return [...new Set(statuses)];
  }, [data?.runs]);

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <span>Root Traces</span>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={onRefresh}
              loading={isLoading}
              disabled={disabled}
            >
              Refresh
            </Button>
          </Space>
        </div>
      }
      className="h-full"
    >
      {/* Filters */}
      <div className="mb-4 space-y-3">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <Input
              placeholder="Search traces..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              disabled={disabled}
            />
          </Col>
          <Col xs={24} sm={6} lg={4}>
            <Select
              placeholder="Status"
              style={{ width: "100%" }}
              allowClear
              value={filters.status}
              onChange={(value) => handleFilterChange("status", value)}
              disabled={disabled}
            >
              {uniqueStatuses.map((status) => (
                <Option key={status} value={status}>
                  {formatters.formatStatus(status).text}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={6} lg={4}>
            <Select
              placeholder="Project"
              style={{ width: "100%" }}
              allowClear
              value={filters.project_name}
              onChange={(value) => handleFilterChange("project_name", value)}
              disabled={disabled}
            >
              {uniqueProjects.map((project) => (
                <Option key={project} value={project}>
                  {project}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={handleSearch}
                disabled={disabled}
              >
                Apply
              </Button>
              <Button
                icon={<ClearOutlined />}
                onClick={handleClearFilters}
                disabled={disabled}
              >
                Clear
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Error State */}
      {error && (
        <Alert
          message="Failed to load traces"
          description={error.message}
          type="error"
          showIcon
          className="mb-4"
        />
      )}

      {/* Table */}
      <Table<TraceRun>
        columns={columns}
        dataSource={data?.runs || []}
        rowKey="id"
        rowSelection={disabled ? undefined : rowSelection}
        loading={isLoading}
        pagination={{
          current: Math.floor(pagination.offset / pagination.limit) + 1,
          pageSize: pagination.limit,
          total: data?.total || 0,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} of ${total} traces`,
          pageSizeOptions: ["25", "50", "100"],
        }}
        onChange={handleTableChange}
        scroll={{ y: 400 }}
        size="small"
        onRow={(record) => ({
          onClick: () => !disabled && onTraceSelect(record.id),
          className: selectedTraceId === record.id ? "bg-blue-50" : "",
        })}
      />
    </Card>
  );
};

export default TraceTable;
