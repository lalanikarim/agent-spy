import React from 'react';
import {
  Card,
  Tree,
  Typography,
  Tag,
  Space,
  Button,
  Alert,
  Descriptions,
  Collapse,
  Empty,
  Tooltip,
  Spin,
} from 'antd';
import {
  CloseOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';

// Extend DataNode to include our custom data
interface TraceDataNode extends DataNode {
  data?: RunHierarchyNode;
}
import { useTraceHierarchy } from '../hooks/useTraces';
import type { RunHierarchyNode } from '../types/traces';
import { formatters } from '../utils/formatters';

const { Text, Title } = Typography;
const { Panel } = Collapse;

interface TraceDetailProps {
  traceId: string | null;
  onClose: () => void;
  disabled?: boolean;
}

const TraceDetail: React.FC<TraceDetailProps> = ({
  traceId,
  onClose,
  disabled = false,
}) => {
  // Fetch trace hierarchy
  const { data, isLoading, error } = useTraceHierarchy(traceId, { enabled: !disabled });

  // Convert hierarchy to tree data
  const convertToTreeData = (node: RunHierarchyNode): TraceDataNode => {
    const { text: statusText, color: statusColor } = formatters.formatStatus(node.status);
    const { icon: typeIcon } = formatters.formatRunType(node.run_type);
    const duration = formatters.formatDuration(node.duration_ms);

    return {
      key: node.id,
      title: (
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-2 flex-1 min-w-0">
            <span>{typeIcon}</span>
            <Text strong className="truncate">
              {formatters.truncateString(node.name, 25)}
            </Text>
            <Tag color={statusColor}>
              {statusText}
            </Tag>
          </div>
          <Text type="secondary" className="text-xs ml-2">
            {duration}
          </Text>
        </div>
      ),
      children: node.children.map(convertToTreeData),
      data: node, // Store the full node data
    };
  };

  // Handle tree node selection
  const [selectedNodeKey, setSelectedNodeKey] = React.useState<string | null>(null);
  const [selectedNode, setSelectedNode] = React.useState<RunHierarchyNode | null>(null);

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
    const { text: statusText, color: statusColor } = formatters.formatStatus(node.status);
    const { text: typeText, icon: typeIcon } = formatters.formatRunType(node.run_type);

    return (
      <div className="space-y-4">
        <Descriptions title="Run Details" size="small" column={1} bordered>
          <Descriptions.Item label="ID">
            <Text copyable className="font-mono text-xs">
              {node.id}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Name">
            <Text strong>{node.name}</Text>
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
              {formatters.formatDuration(node.duration_ms)}
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

        {/* Inputs/Outputs/Error */}
        <Collapse size="small">
          {node.inputs && (
            <Panel header="Inputs" key="inputs" extra={<CodeOutlined />}>
              <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                {formatters.formatJSON(node.inputs)}
              </pre>
            </Panel>
          )}
          {node.outputs && (
            <Panel header="Outputs" key="outputs" extra={<CodeOutlined />}>
              <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                {formatters.formatJSON(node.outputs)}
              </pre>
            </Panel>
          )}
          {node.error && (
            <Panel header="Error" key="error" extra={<InfoCircleOutlined className="text-red-500" />}>
              <Text type="danger" className="text-sm">
                {node.error}
              </Text>
            </Panel>
          )}
          {node.extra && (
            <Panel header="Extra Data" key="extra" extra={<InfoCircleOutlined />}>
              <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-40">
                {formatters.formatJSON(node.extra)}
              </pre>
            </Panel>
          )}
        </Collapse>
      </div>
    );
  };

  if (!traceId) {
    return (
      <Card title="Trace Details" className="h-full">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="Select a trace to view details"
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <div className="flex items-center justify-between">
          <Space>
            <BranchesOutlined />
            <span>Trace Hierarchy</span>
            {data && (
              <Tag color="blue">
                {data.total_runs} runs, depth {data.max_depth}
              </Tag>
            )}
          </Space>
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={onClose}
            disabled={disabled}
          />
        </div>
      }
      className="h-full"
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

      {data && (
        <div className="space-y-4">
          {/* Hierarchy Overview */}
          <div className="bg-gray-50 p-3 rounded">
            <Space split={<span className="text-gray-300">|</span>}>
              <span className="text-sm">
                <ClockCircleOutlined className="mr-1" />
                Started: {formatters.formatRelativeTime(data.hierarchy.start_time)}
              </span>
              <span className="text-sm">
                Duration: {formatters.formatDuration(data.hierarchy.duration_ms)}
              </span>
              <span className="text-sm">
                Status: <Tag color={formatters.formatStatus(data.hierarchy.status).color}>
                  {formatters.formatStatus(data.hierarchy.status).text}
                </Tag>
              </span>
            </Space>
          </div>

          {/* Tree View */}
          <div className="hierarchy-scroll max-h-96 overflow-auto">
            <Tree
              className="trace-hierarchy-tree"
              treeData={[convertToTreeData(data.hierarchy)]}
              defaultExpandAll
              showLine={{ showLeafIcon: false }}
              onSelect={handleNodeSelect}
              selectedKeys={selectedNodeKey ? [selectedNodeKey] : []}
            />
          </div>

          {/* Selected Node Details */}
          {selectedNode && (
            <div className="border-t pt-4">
              <Title level={5} className="mb-3">
                Node Details
              </Title>
              {renderNodeDetails(selectedNode)}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default TraceDetail;
