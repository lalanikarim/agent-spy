import {
  WifiOutlined as WifiOffOutlined,
  WifiOutlined,
} from "@ant-design/icons";
import { Space, Switch, Tooltip } from "antd";
import React from "react";

interface ConnectionStatusProps {
  isConnected: boolean;
  connectionError: string | null;
  subscribedEvents: string[];
  onToggleRealtime?: (enabled: boolean) => void;
  realtimeEnabled?: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  connectionError,
  subscribedEvents,
  onToggleRealtime,
  realtimeEnabled = true,
}) => {
  const getStatusText = () => {
    if (connectionError) return "Connection Error";
    if (isConnected) return "Live Updates";
    return "Disconnected";
  };

  const getStatusIcon = () => {
    if (isConnected) {
      return <WifiOutlined style={{ color: "#52c41a" }} />;
    }
    return <WifiOffOutlined style={{ color: "#ff4d4f" }} />;
  };

  const getTooltipContent = () => {
    if (connectionError) {
      return `Connection Error: ${connectionError}`;
    }
    if (isConnected) {
      return `Connected - Subscribed to ${subscribedEvents.length} event types`;
    }
    return "Disconnected - Attempting to reconnect...";
  };

  return (
    <Space size="small">
      <Tooltip title={getTooltipContent()}>
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span
            style={{
              fontSize: "12px",
              color: isConnected ? "#52c41a" : "#ff4d4f",
            }}
          >
            {getStatusText()}
          </span>
        </div>
      </Tooltip>

      {onToggleRealtime && (
        <Space size="small">
          <span style={{ fontSize: "12px", color: "#666" }}>Real-time:</span>
          <Switch
            size="small"
            checked={realtimeEnabled && isConnected}
            disabled={!isConnected}
            onChange={onToggleRealtime}
            title={
              !isConnected
                ? "Enable WebSocket connection first"
                : "Toggle real-time updates"
            }
          />
        </Space>
      )}
    </Space>
  );
};

export default ConnectionStatus;
