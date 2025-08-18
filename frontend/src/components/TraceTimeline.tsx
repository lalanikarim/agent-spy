import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import React, { useEffect, useRef } from "react";
import { DataSet } from "vis-data";
import { Timeline } from "vis-timeline/standalone";
import "vis-timeline/styles/vis-timeline-graph2d.css";
import type { RunHierarchyNode } from "../types/traces";
import { formatters } from "../utils/formatters";

// Extend dayjs with UTC plugin
dayjs.extend(utc);

interface TraceTimelineProps {
  hierarchy: RunHierarchyNode;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string) => void;
}

export const TraceTimeline: React.FC<TraceTimelineProps> = ({
  hierarchy,
  selectedNodeId,
  onNodeSelect,
}) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const timelineInstance = useRef<Timeline | null>(null);

  useEffect(() => {
    if (!timelineRef.current) return;

    // Collect all nodes from the hierarchy
    const collectNodes = (
      node: RunHierarchyNode,
      depth: number = 0
    ): Array<{
      id: string;
      content: string;
      start: Date;
      end?: Date;
      group: number;
      className: string;
      title: string;
      type: string;
      status: string;
    }> => {
      const items = [];

      if (node.start_time) {
        const { icon: typeIcon } = formatters.formatRunType(node.run_type);

        items.push({
          id: node.id,
          content: `${typeIcon} ${formatters.truncateString(node.name, 20)}`,
          start: dayjs.utc(node.start_time).toDate(),
          end: node.end_time ? dayjs.utc(node.end_time).toDate() : undefined,
          group: depth,
          className: `timeline-item-${node.status} ${
            selectedNodeId === node.id ? "selected" : ""
          }`,
          title: `${node.name}\nType: ${node.run_type}\nStatus: ${
            node.status
          }\nDuration: ${formatters.formatTaskDuration(
            node.duration_ms,
            node.start_time,
            node.end_time || null,
            node.status
          )}`,
          type: node.end_time ? "range" : "point",
          status: node.status,
        });
      }

      // Add children
      for (const child of node.children) {
        items.push(...collectNodes(child, depth + 1));
      }

      return items;
    };

    const items = collectNodes(hierarchy);
    const groups = new DataSet(
      Array.from(new Set(items.map((item) => item.group))).map((groupId) => ({
        id: groupId,
        content: `Level ${groupId}`,
        order: groupId,
      }))
    );

    const dataset = new DataSet(items);

    const options = {
      height: "300px",
      stack: false,
      showCurrentTime: false,
      zoomable: true,
      moveable: true,
      orientation: "top",
      margin: {
        item: 10,
        axis: 20,
      },
      format: {
        minorLabels: {
          millisecond: "SSS",
          second: "HH:mm:ss",
          minute: "HH:mm",
          hour: "HH:mm",
          weekday: "ddd D",
          day: "D",
          week: "w",
          month: "MMM",
          year: "YYYY",
        },
        majorLabels: {
          millisecond: "HH:mm:ss",
          second: "D MMMM HH:mm",
          minute: "ddd D MMMM",
          hour: "ddd D MMMM",
          weekday: "MMMM YYYY",
          day: "MMMM YYYY",
          week: "MMMM YYYY",
          month: "YYYY",
          year: "",
        },
      },
      tooltip: {
        followMouse: true,
        overflowMethod: "cap" as const,
      },
    };

    // Create timeline
    timelineInstance.current = new Timeline(
      timelineRef.current,
      dataset,
      groups,
      options
    );

    // Add click handler
    timelineInstance.current.on("select", (properties) => {
      if (properties.items.length > 0 && onNodeSelect) {
        onNodeSelect(properties.items[0]);
      }
    });

    // Cleanup
    return () => {
      if (timelineInstance.current) {
        timelineInstance.current.destroy();
        timelineInstance.current = null;
      }
    };
  }, [hierarchy, selectedNodeId, onNodeSelect]);

  // Update selection when selectedNodeId changes
  useEffect(() => {
    if (timelineInstance.current && selectedNodeId) {
      timelineInstance.current.setSelection([selectedNodeId]);
    }
  }, [selectedNodeId]);

  return (
    <div className="w-full">
      <div
        className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300"
        style={{ color: "var(--color-text)" }}
      >
        Execution Timeline
      </div>
      <div
        ref={timelineRef}
        className="border rounded bg-white timeline-container"
        style={{ minHeight: "300px" }}
      />
      <style>{`
        .timeline-container .vis-item.timeline-item-completed {
          background-color: #52c41a;
          border-color: #389e0d;
          color: white;
        }
        .timeline-container .vis-item.timeline-item-running {
          background-color: #1890ff;
          border-color: #096dd9;
          color: white;
        }
        .timeline-container .vis-item.timeline-item-failed {
          background-color: #ff4d4f;
          border-color: #cf1322;
          color: white;
        }
        .timeline-container .vis-item.selected {
          box-shadow: 0 0 0 2px #1890ff;
        }
        .timeline-container .vis-group-label {
          font-size: 12px;
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};
