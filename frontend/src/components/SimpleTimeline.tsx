import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { RunHierarchyNode } from '../types/traces';
import { formatters } from '../utils/formatters';

interface SimpleTimelineProps {
  hierarchy: RunHierarchyNode;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string) => void;
}

export const SimpleTimeline: React.FC<SimpleTimelineProps> = ({
  hierarchy,
  selectedNodeId,
  onNodeSelect,
}) => {
  // Flatten hierarchy and calculate timeline data
  const collectTimelineData = (node: RunHierarchyNode, depth: number = 0): Array<{
    id: string;
    name: string;
    start: number;
    duration: number;
    depth: number;
    status: string;
    type: string;
    fullName: string;
  }> => {
    const items = [];
    
    if (node.start_time && node.end_time) {
      const start = new Date(node.start_time).getTime();
      const end = new Date(node.end_time).getTime();
      const duration = end - start;
      
      items.push({
        id: node.id,
        name: formatters.truncateString(node.name, 15),
        start,
        duration,
        depth,
        status: node.status,
        type: node.run_type,
        fullName: node.name,
      });
    }

    // Add children
    for (const child of node.children) {
      items.push(...collectTimelineData(child, depth + 1));
    }

    return items;
  };

  const timelineData = collectTimelineData(hierarchy);
  
  // Sort by start time
  timelineData.sort((a, b) => a.start - b.start);
  
  // Calculate relative start times from the first event
  const firstStart = timelineData.length > 0 ? timelineData[0].start : 0;
  const chartData = timelineData.map((item, index) => ({
    ...item,
    relativeStart: (item.start - firstStart) / 1000, // Convert to seconds
    relativeDuration: item.duration / 1000, // Convert to seconds
    index,
    color: getStatusColor(item.status),
    selected: item.id === selectedNodeId,
  }));

  function getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return '#52c41a';
      case 'running': return '#1890ff';
      case 'failed': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-medium">{data.fullName}</p>
          <p className="text-sm text-gray-600">Type: {data.type}</p>
          <p className="text-sm text-gray-600">Status: {data.status}</p>
          <p className="text-sm text-gray-600">Duration: {formatters.formatDuration(data.duration)}</p>
          <p className="text-sm text-gray-600">Start: +{data.relativeStart.toFixed(2)}s</p>
        </div>
      );
    }
    return null;
  };

  const handleBarClick = (data: any) => {
    if (onNodeSelect && data.id) {
      onNodeSelect(data.id);
    }
  };

  return (
    <div className="w-full">
      <div className="mb-2 text-sm font-medium text-gray-700">Execution Timeline (Gantt Chart)</div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          layout="horizontal"
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            domain={[0, 'dataMax']}
            tickFormatter={(value) => `${value.toFixed(1)}s`}
            label={{ value: 'Time (seconds)', position: 'insideBottom', offset: -5 }}
          />
          <YAxis 
            type="category" 
            dataKey="name"
            width={120}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="relativeDuration"
            fill="#3B82F6"
            onClick={handleBarClick}
            cursor="pointer"
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 rounded"></div>
          <span>Running</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Failed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-400 rounded"></div>
          <span>Other</span>
        </div>
      </div>
    </div>
  );
};
