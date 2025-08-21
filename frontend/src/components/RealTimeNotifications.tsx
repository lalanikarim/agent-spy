import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from "@ant-design/icons";
import { notification } from "antd";
import React, { useEffect } from "react";

interface RealTimeNotificationsProps {
  isConnected: boolean;
  subscribedEvents: string[];
}

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

const RealTimeNotifications: React.FC<RealTimeNotificationsProps> = ({
  isConnected,
  subscribedEvents,
}) => {
  // const notificationRef = useRef<{ [key: string]: string }>({});

  useEffect(() => {
    // Listen for WebSocket messages from the global WebSocket hook
    const handleWebSocketMessage = (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleNotification(message);
      } catch (error) {
        console.error(
          "Failed to parse WebSocket message for notifications:",
          error
        );
      }
    };

    // Add event listener to window for WebSocket messages
    window.addEventListener("websocket-message", handleWebSocketMessage as any);

    return () => {
      window.removeEventListener(
        "websocket-message",
        handleWebSocketMessage as any
      );
    };
  }, [subscribedEvents]);

  const handleNotification = (message: WebSocketMessage) => {
    if (!isConnected || !subscribedEvents.includes(message.type)) {
      return;
    }

    switch (message.type) {
      case "trace.created":
        showTraceCreatedNotification(message.data);
        break;
      case "trace.completed":
        showTraceCompletedNotification(message.data);
        break;
      case "trace.failed":
        showTraceFailedNotification(message.data);
        break;
      case "trace.updated":
        // Only show notification for significant updates
        if (message.data.changes?.status) {
          showTraceStatusChangedNotification(message.data);
        }
        break;
    }
  };

  const showTraceCreatedNotification = (data: any) => {
    const key = `trace-created-${data.id}`;
    notification.info({
      key,
      message: "New Trace Created",
      description: (
        <div>
          <div>
            <strong>{data.name}</strong>
          </div>
          <div>Type: {data.run_type}</div>
          <div>Project: {data.project_name}</div>
        </div>
      ),
      icon: <InfoCircleOutlined style={{ color: "#1890ff" }} />,
      placement: "topRight",
      duration: 5,
      onClick: () => {
        // Could navigate to the trace detail view
        console.log("Navigate to trace:", data.id);
      },
    });
  };

  const showTraceCompletedNotification = (data: any) => {
    const key = `trace-completed-${data.id}`;
    notification.success({
      key,
      message: "Trace Completed",
      description: (
        <div>
          <div>
            <strong>{data.name}</strong>
          </div>
          <div>Duration: {formatDuration(data.duration_ms)}</div>
          <div>Project: {data.project_name}</div>
        </div>
      ),
      icon: <CheckCircleOutlined style={{ color: "#52c41a" }} />,
      placement: "topRight",
      duration: 6,
      onClick: () => {
        console.log("Navigate to completed trace:", data.id);
      },
    });
  };

  const showTraceFailedNotification = (data: any) => {
    const key = `trace-failed-${data.id}`;
    notification.error({
      key,
      message: "Trace Failed",
      description: (
        <div>
          <div>
            <strong>{data.name}</strong>
          </div>
          <div>Error: {data.error || "Unknown error"}</div>
          <div>Project: {data.project_name}</div>
        </div>
      ),
      icon: <CloseCircleOutlined style={{ color: "#ff4d4f" }} />,
      placement: "topRight",
      duration: 8,
      onClick: () => {
        console.log("Navigate to failed trace:", data.id);
      },
    });
  };

  const showTraceStatusChangedNotification = (data: any) => {
    const key = `trace-status-${data.id}`;
    const status = data.status;

    if (status === "completed") {
      notification.success({
        key,
        message: "Trace Status Changed",
        description: (
          <div>
            <div>
              <strong>{data.name}</strong> is now completed
            </div>
            <div>Project: {data.project_name}</div>
          </div>
        ),
        icon: <CheckCircleOutlined style={{ color: "#52c41a" }} />,
        placement: "topRight",
        duration: 4,
      });
    } else if (status === "failed") {
      notification.error({
        key,
        message: "Trace Status Changed",
        description: (
          <div>
            <div>
              <strong>{data.name}</strong> has failed
            </div>
            <div>Project: {data.project_name}</div>
          </div>
        ),
        icon: <ExclamationCircleOutlined style={{ color: "#ff4d4f" }} />,
        placement: "topRight",
        duration: 6,
      });
    }
  };

  const formatDuration = (durationMs: number | null): string => {
    if (!durationMs) return "Unknown";

    if (durationMs < 1000) {
      return `${durationMs}ms`;
    } else if (durationMs < 60000) {
      return `${(durationMs / 1000).toFixed(1)}s`;
    } else {
      const minutes = Math.floor(durationMs / 60000);
      const seconds = ((durationMs % 60000) / 1000).toFixed(0);
      return `${minutes}m ${seconds}s`;
    }
  };

  // This component doesn't render anything visible
  return null;
};

export default RealTimeNotifications;
