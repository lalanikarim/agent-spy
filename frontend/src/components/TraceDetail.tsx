import {
  BarChartOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  CodeOutlined,
  CompressOutlined,
  CopyOutlined,
  ExpandOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Collapse,
  Descriptions,
  Empty,
  Space,
  Spin,
  Tabs,
  Tag,
  Tooltip,
  Tree,
  Typography,
} from "antd";
import type { DataNode } from "antd/es/tree";
import React from "react";
import { useTraceHierarchy, useRealTimeUpdates } from "../hooks/useTraces";
import type { RunHierarchyNode } from "../types/traces";
import { formatters } from "../utils/formatters";
import { SimpleTimeline } from "./SimpleTimeline";
import { TraceTimeline } from "./TraceTimeline";
import Card from "./ui/Card";

// Extend DataNode to include our custom data
interface TraceDataNode extends DataNode {
  data?: RunHierarchyNode;
}

const { Text, Title } = Typography;
const { Panel } = Collapse;

interface TraceDetailProps {
  traceId: string | null;
  onClose: () => void;
  onToggleExpansion: () => void;
  isExpanded: boolean;
  refreshTrigger: number;
  onRefresh?: () => void;
  refreshLoading?: boolean;
  disabled?: boolean;
}

const TraceDetail: React.FC<TraceDetailProps> = ({
  traceId,
  onClose,
  onToggleExpansion,
  isExpanded,
  refreshTrigger,
  onRefresh,
  refreshLoading = false,
  disabled = false,
}) => {
  // Real-time updates for elapsed time
  useRealTimeUpdates(2000); // Update every 2 seconds

  // Fetch trace hierarchy
  const { data, isLoading, error, refetch } = useTraceHierarchy(traceId, {
    enabled: !disabled,
  });

  // Trigger refetch when refreshTrigger changes
  React.useEffect(() => {
    if (refreshTrigger > 0 && traceId) {
      refetch();
    }
  }, [refreshTrigger, traceId, refetch]);

  // Helper function to copy text to clipboard
  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Using a simple notification approach without message component
      console.log(`${label} copied to clipboard`);
    } catch (err) {
      console.error("Failed to copy to clipboard:", err);
    }
  };

  // Copy entire tree hierarchy as JSON
  const copyTreeJson = async () => {
    if (!data?.hierarchy) return;

    try {
      setCopyLoading(true);
      const jsonString = JSON.stringify(data.hierarchy, null, 2);
      await copyToClipboard(jsonString, "Tree JSON");
    } catch (error) {
      console.error("Failed to copy tree JSON:", error);
    } finally {
      setCopyLoading(false);
    }
  };

  // Convert hierarchy to tree data
  const convertToTreeData = (node: RunHierarchyNode): TraceDataNode => {
    const { text: statusText, color: statusColor } = formatters.formatStatus(
      node.status
    );
    const { icon: typeIcon } = formatters.formatRunType(node.run_type);
    const duration = formatters.formatTaskDuration(
      node.duration_ms,
      node.start_time,
      node.end_time,
      node.status
    );

    return {
      key: node.id,
      title: (
        <div className="flex items-center justify-between w-full max-w-full overflow-hidden">
          <div className="flex items-center space-x-2 flex-1 min-w-0 overflow-hidden">
            <span>{typeIcon}</span>
            <Text strong className="truncate max-w-full overflow-hidden">
              {formatters.truncateString(node.name, 35)}
            </Text>
            <Tag color={statusColor}>{statusText}</Tag>
          </div>
          <Text type="secondary" className="text-xs ml-2 flex-shrink-0">
            {duration}
          </Text>
        </div>
      ),
      children: node.children?.map(convertToTreeData) || [],
      data: node, // Store the full node data
    };
  };

  // Handle tree node selection
  const [selectedNodeKey, setSelectedNodeKey] = React.useState<string | null>(
    null
  );
  const [selectedNode, setSelectedNode] =
    React.useState<RunHierarchyNode | null>(null);

  // Copy tree JSON loading state
  const [copyLoading, setCopyLoading] = React.useState<boolean>(false);

  // Clear selected node when trace changes
  React.useEffect(() => {
    setSelectedNodeKey(null);
    setSelectedNode(null);
  }, [traceId]);

  const handleNodeSelect = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      const key = selectedKeys[0] as string;
      const nodeData = info.node.data as RunHierarchyNode;
      setSelectedNodeKey(key);
      setSelectedNode(nodeData);
    } else {
      setSelectedNodeKey(null);
      setSelectedNode(null);
    }
  };

  // Render node details
  const renderNodeDetails = (node: RunHierarchyNode) => {
    const { text: statusText, color: statusColor } = formatters.formatStatus(
      node.status
    );
    const { text: typeText, icon: typeIcon } = formatters.formatRunType(
      node.run_type
    );

    return (
      <div className="space-y-4">
        <div className="max-w-full">
          <Descriptions
            size="small"
            column={1}
            bordered
            layout="horizontal"
            labelStyle={{ width: "100px", minWidth: "100px" }}
          >
            <Descriptions.Item label="ID">
              <Text copyable className="font-mono text-xs break-all">
                {node.id}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Name">
              <Text
                strong
                className="break-words"
                copyable={{ text: node.name }}
              >
                {node.name}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Type">
              <Space>
                <span>{typeIcon}</span>
                <Text>{typeText}</Text>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={statusColor}>{statusText}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Duration">
              <Text className="font-mono">
                {formatters.formatTaskDuration(
                  node.duration_ms,
                  node.start_time,
                  node.end_time,
                  node.status
                )}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Started">
              <Tooltip title={formatters.formatDateTime(node.start_time)}>
                <Text>{formatters.formatRelativeTime(node.start_time)}</Text>
              </Tooltip>
            </Descriptions.Item>
            {node.end_time && (
              <Descriptions.Item label="Ended">
                <Tooltip title={formatters.formatDateTime(node.end_time)}>
                  <Text>{formatters.formatRelativeTime(node.end_time)}</Text>
                </Tooltip>
              </Descriptions.Item>
            )}
          </Descriptions>
        </div>

        {/* Inputs/Outputs/Error */}
        <div
          className="w-full overflow-hidden"
          style={{
            width: "100%",
            boxSizing: "border-box",
          }}
        >
          <Collapse
            size="small"
            className="w-full border-gray-200 dark:border-gray-600"
            style={{
              width: "100%",
              boxSizing: "border-box",
              borderColor: "var(--color-border)",
            }}
          >
            {node.inputs && (
              <Panel
                header="Inputs"
                key="inputs"
                extra={
                  <Space>
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined style={{ color: "#1890ff" }} />}
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(
                          formatters.formatJSON(node.inputs),
                          "Inputs"
                        );
                      }}
                      title="Copy inputs"
                    />
                    <CodeOutlined />
                  </Space>
                }
              >
                <div
                  className="max-h-32 overflow-auto w-full"
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                  }}
                >
                  <pre
                    className="text-xs bg-gray-50 dark:bg-gray-700 p-2 rounded-lg border border-gray-200 dark:border-gray-600 whitespace-pre overflow-x-auto overflow-y-auto block w-full"
                    style={{
                      width: "100%",
                      minWidth: "0",
                      wordWrap: "break-word",
                      wordBreak: "break-all",
                      boxSizing: "border-box",
                      backgroundColor: "var(--color-surface-hover)",
                      borderColor: "var(--color-border-hover)",
                    }}
                  >
                    {formatters.formatJSON(node.inputs)}
                  </pre>
                </div>
              </Panel>
            )}
            {node.outputs && (
              <Panel
                header="Outputs"
                key="outputs"
                extra={
                  <Space>
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined style={{ color: "#1890ff" }} />}
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(
                          formatters.formatJSON(node.outputs),
                          "Outputs"
                        );
                      }}
                      title="Copy outputs"
                    />
                    <CodeOutlined />
                  </Space>
                }
              >
                <div
                  className="max-h-32 overflow-auto w-full"
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                  }}
                >
                  <pre
                    className="text-xs bg-gray-50 dark:bg-gray-700 p-2 rounded-lg border border-gray-200 dark:border-gray-600 whitespace-pre overflow-x-auto overflow-y-auto block w-full"
                    style={{
                      width: "100%",
                      minWidth: "0",
                      wordWrap: "break-word",
                      wordBreak: "break-all",
                      boxSizing: "border-box",
                      backgroundColor: "var(--color-surface-hover)",
                      borderColor: "var(--color-border-hover)",
                    }}
                  >
                    {formatters.formatJSON(node.outputs)}
                  </pre>
                </div>
              </Panel>
            )}
            {node.error && (
              <Panel
                header="Error"
                key="error"
                extra={
                  <Space>
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined style={{ color: "#1890ff" }} />}
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(node.error!, "Error");
                      }}
                      title="Copy error"
                    />
                    <InfoCircleOutlined className="text-red-500" />
                  </Space>
                }
              >
                <div
                  className="max-h-32 overflow-auto w-full max-w-full"
                  style={{
                    width: "100%",
                    maxWidth: "100%",
                    boxSizing: "border-box",
                  }}
                >
                  <div
                    className="text-xs text-red-600 whitespace-pre overflow-x-auto overflow-y-auto p-2 bg-red-50 rounded-lg border border-red-200 max-w-full"
                    style={{
                      width: "100%",
                      maxWidth: "100%",
                      minWidth: "0",
                      wordWrap: "break-word",
                      wordBreak: "break-all",
                      boxSizing: "border-box",
                    }}
                  >
                    {node.error}
                  </div>
                </div>
              </Panel>
            )}
            {node.extra && (
              <Panel
                header="Extra Data"
                key="extra"
                extra={
                  <Space>
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined style={{ color: "#1890ff" }} />}
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(
                          formatters.formatJSON(node.extra),
                          "Extra data"
                        );
                      }}
                      title="Copy extra data"
                    />
                    <InfoCircleOutlined />
                  </Space>
                }
              >
                <div
                  className="max-h-32 overflow-auto w-full"
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                  }}
                >
                  <pre
                    className="text-xs bg-gray-50 dark:bg-gray-700 p-2 rounded-lg border border-gray-200 dark:border-gray-600 whitespace-pre overflow-x-auto overflow-y-auto block w-full"
                    style={{
                      width: "100%",
                      minWidth: "0",
                      wordWrap: "break-word",
                      wordBreak: "break-all",
                      boxSizing: "border-box",
                      backgroundColor: "var(--color-surface-hover)",
                      borderColor: "var(--color-border-hover)",
                    }}
                  >
                    {formatters.formatJSON(node.extra)}
                  </pre>
                </div>
              </Panel>
            )}
          </Collapse>
        </div>
      </div>
    );
  };

  if (!traceId) {
    return (
      <Card className="h-full">
        <div
          className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4"
          style={{ color: "var(--color-text)" }}
        >
          Trace Details
        </div>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Select a trace to view details"
        />
      </Card>
    );
  }

  return (
    <Card
      className={`h-full flex flex-col ${
        isExpanded ? "" : "max-w-full w-full"
      }`}
      style={
        !isExpanded
          ? {
              width: "100%",
              maxWidth: "460px",
              minWidth: "460px",
              overflow: "hidden",
            }
          : {}
      }
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <Space>
          <BranchesOutlined />
          <span
            className="text-lg font-semibold text-gray-900 dark:text-gray-100"
            style={{ color: "var(--color-text)" }}
          >
            Trace Hierarchy
          </span>
          {data && (
            <>
              <Tag color="blue">
                {data.total_runs} runs, depth {data.max_depth}
              </Tag>
              <Button
                type="text"
                icon={<CopyOutlined style={{ color: "#1890ff" }} />}
                onClick={copyTreeJson}
                loading={copyLoading}
                disabled={disabled || !data}
                title="Copy tree JSON"
              />
            </>
          )}
        </Space>
        <Space>
          <Button
            type="text"
            icon={isExpanded ? <CompressOutlined /> : <ExpandOutlined />}
            onClick={onToggleExpansion}
            disabled={disabled}
            title={isExpanded ? "Collapse to sidebar" : "Expand to full screen"}
          />
          {isExpanded && onRefresh && (
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={onRefresh}
              loading={refreshLoading}
              disabled={disabled}
              title="Refresh trace hierarchy"
            />
          )}
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={onClose}
            disabled={disabled}
            title="Close trace details"
          />
        </Space>
      </div>

      {/* Content */}
      <div
        className="flex-1 overflow-hidden"
        style={{
          padding: isExpanded ? "0" : "0",
          width: "100%",
          boxSizing: "border-box",
          overflow: "hidden",
        }}
      >
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Spin size="large" />
          </div>
        )}

        {error && (
          <Alert
            message="Failed to load trace hierarchy"
            description={error.message}
            type="error"
            showIcon
            className="mb-4"
          />
        )}

        {data &&
          (isExpanded ? (
            // Expanded Mode: Side-by-side layout (hierarchy left, details right)
            <div className="flex h-full space-x-6 overflow-hidden">
              {/* Left Panel: Hierarchy Overview + Tree View */}
              <div className="flex flex-col w-1/2 space-y-4 overflow-hidden">
                {/* Hierarchy Overview */}
                <div
                  className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg border border-gray-200 dark:border-gray-600 flex-shrink-0"
                  style={{
                    backgroundColor: "var(--color-surface-hover)",
                    borderColor: "var(--color-border)",
                  }}
                >
                  <Space
                    split={
                      <span
                        className="text-gray-300 dark:text-gray-500"
                        style={{ color: "var(--color-text-muted)" }}
                      >
                        |
                      </span>
                    }
                    wrap
                  >
                    <span className="text-sm">
                      <ClockCircleOutlined className="mr-1" />
                      Started:{" "}
                      {formatters.formatRelativeTime(data.hierarchy.start_time)}
                    </span>
                    <span className="text-sm">
                      Duration:{" "}
                      {formatters.formatTaskDuration(
                        data.hierarchy.duration_ms,
                        data.hierarchy.start_time,
                        data.hierarchy.end_time,
                        data.hierarchy.status
                      )}
                    </span>
                    <span className="text-sm">
                      Status:{" "}
                      <Tag
                        color={
                          formatters.formatStatus(data.hierarchy.status).color
                        }
                      >
                        {formatters.formatStatus(data.hierarchy.status).text}
                      </Tag>
                    </span>
                  </Space>
                </div>

                {/* Tree View and Timeline - Full height in expanded mode */}
                <div
                  className="flex-1 overflow-hidden border border-gray-200 dark:border-gray-600 rounded-lg"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  <div className="px-4 pt-2">
                    <Tabs
                      defaultActiveKey="tree"
                      size="small"
                      className="h-full"
                      items={[
                        {
                          key: "tree",
                          label: (
                            <span>
                              <BranchesOutlined />
                              Tree View
                            </span>
                          ),
                          children: (
                            <div className="h-full overflow-auto p-3">
                              <Tree
                                className="trace-hierarchy-tree"
                                style={{ width: "100%", overflow: "hidden" }}
                                treeData={[convertToTreeData(data.hierarchy)]}
                                defaultExpandAll
                                showLine={{ showLeafIcon: false }}
                                onSelect={handleNodeSelect}
                                selectedKeys={
                                  selectedNodeKey ? [selectedNodeKey] : []
                                }
                              />
                            </div>
                          ),
                        },
                        {
                          key: "timeline",
                          label: (
                            <span>
                              <BarChartOutlined />
                              Timeline
                            </span>
                          ),
                          children: (
                            <div className="h-full overflow-auto p-4">
                              <TraceTimeline
                                hierarchy={data.hierarchy}
                                selectedNodeId={selectedNodeKey || undefined}
                                onNodeSelect={(nodeId) => {
                                  setSelectedNodeKey(nodeId);
                                  const findNode = (
                                    node: RunHierarchyNode
                                  ): RunHierarchyNode | null => {
                                    if (node.id === nodeId) return node;
                                    for (const child of node.children) {
                                      const found = findNode(child);
                                      if (found) return found;
                                    }
                                    return null;
                                  };
                                  const node = findNode(data.hierarchy);
                                  if (node) setSelectedNode(node);
                                }}
                              />
                            </div>
                          ),
                        },
                        {
                          key: "gantt",
                          label: (
                            <span>
                              <ClockCircleOutlined />
                              Gantt Chart
                            </span>
                          ),
                          children: (
                            <div className="h-full overflow-auto p-4">
                              <SimpleTimeline
                                hierarchy={data.hierarchy}
                                selectedNodeId={selectedNodeKey || undefined}
                                onNodeSelect={(nodeId) => {
                                  setSelectedNodeKey(nodeId);
                                  const findNode = (
                                    node: RunHierarchyNode
                                  ): RunHierarchyNode | null => {
                                    if (node.id === nodeId) return node;
                                    for (const child of node.children) {
                                      const found = findNode(child);
                                      if (found) return found;
                                    }
                                    return null;
                                  };
                                  const node = findNode(data.hierarchy);
                                  if (node) setSelectedNode(node);
                                }}
                              />
                            </div>
                          ),
                        },
                      ]}
                    />
                  </div>
                </div>
              </div>

              {/* Right Panel: Node Details */}
              <div className="flex flex-col w-1/2 overflow-hidden">
                {selectedNode ? (
                  <div className="flex flex-col h-full overflow-hidden">
                    <Title level={5} className="mb-3 flex-shrink-0">
                      Node Details
                    </Title>
                    <div className="flex-1 overflow-auto">
                      {renderNodeDetails(selectedNode)}
                    </div>
                  </div>
                ) : (
                  <div
                    className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400"
                    style={{ color: "var(--color-text-secondary)" }}
                  >
                    <div className="text-center">
                      <span className="text-4xl mb-2 block">🔍</span>
                      <p>Select a node from the hierarchy to view details</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            // Compact Mode: Stacked layout (current behavior)
            <div
              className="flex flex-col h-full space-y-4 overflow-hidden w-full"
              style={{
                width: "100%",
                boxSizing: "border-box",
                overflow: "hidden",
              }}
            >
              {/* Hierarchy Overview */}
              <div
                className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg border border-gray-200 dark:border-gray-600 flex-shrink-0"
                style={{
                  backgroundColor: "var(--color-surface-hover)",
                  borderColor: "var(--color-border)",
                }}
              >
                <Space
                  split={
                    <span
                      className="text-gray-300 dark:text-gray-500"
                      style={{ color: "var(--color-text-muted)" }}
                    >
                      |
                    </span>
                  }
                  wrap
                >
                  <span className="text-sm">
                    <ClockCircleOutlined className="mr-1" />
                    Started:{" "}
                    {formatters.formatRelativeTime(data.hierarchy.start_time)}
                  </span>
                  <span className="text-sm">
                    Duration:{" "}
                    {formatters.formatTaskDuration(
                      data.hierarchy.duration_ms,
                      data.hierarchy.start_time,
                      data.hierarchy.end_time,
                      data.hierarchy.status
                    )}
                  </span>
                  <span className="text-sm">
                    Status:{" "}
                    <Tag
                      color={
                        formatters.formatStatus(data.hierarchy.status).color
                      }
                    >
                      {formatters.formatStatus(data.hierarchy.status).text}
                    </Tag>
                  </span>
                </Space>
              </div>

              {/* Tree View - Limited height in compact mode */}
              <div
                className="flex-shrink-0 max-h-48 overflow-auto border border-gray-200 dark:border-gray-600 rounded-lg w-full p-3"
                style={{ borderColor: "var(--color-border)" }}
              >
                <Tree
                  className="trace-hierarchy-tree w-full"
                  style={{
                    width: "100%",
                    overflow: "hidden",
                  }}
                  treeData={[convertToTreeData(data.hierarchy)]}
                  defaultExpandAll
                  showLine={{ showLeafIcon: false }}
                  onSelect={handleNodeSelect}
                  selectedKeys={selectedNodeKey ? [selectedNodeKey] : []}
                />
              </div>

              {/* Selected Node Details - Below tree in compact mode */}
              {selectedNode && (
                <div
                  className="flex-1 border-t border-gray-200 dark:border-gray-600 pt-4 overflow-auto min-h-0 w-full"
                  style={{ borderTopColor: "var(--color-border)" }}
                >
                  <Title level={5} className="mb-3">
                    Node Details
                  </Title>
                  <div className="overflow-auto w-full">
                    {renderNodeDetails(selectedNode)}
                  </div>
                </div>
              )}
            </div>
          ))}
      </div>
    </Card>
  );
};

export default TraceDetail;
