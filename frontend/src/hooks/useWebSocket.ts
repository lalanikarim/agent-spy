import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface WebSocketState {
  isConnected: boolean;
  connectionError: string | null;
  subscribedEvents: string[];
}

export const useWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    connectionError: null,
    subscribedEvents: [],
  });
  const queryClient = useQueryClient();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 5000; // 5 seconds

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const wsUrl =
      import.meta.env.API_WS_URL ||
      import.meta.env.VITE_WS_URL ||
      `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setState((prev) => ({
        ...prev,
        isConnected: true,
        connectionError: null,
      }));
      reconnectAttemptsRef.current = 0;
      console.log("🔌 WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.onclose = (event) => {
      setState((prev) => ({
        ...prev,
        isConnected: false,
      }));
      console.log("🔌 WebSocket disconnected", event.code, event.reason);

      // Attempt reconnection if not a normal closure
      if (
        event.code !== 1000 &&
        reconnectAttemptsRef.current < maxReconnectAttempts
      ) {
        reconnectAttemptsRef.current++;
        console.log(
          `🔄 Attempting reconnection ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`
        );

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectDelay);
      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setState((prev) => ({
          ...prev,
          connectionError: "Failed to reconnect after multiple attempts",
        }));
      }
    };

    ws.onerror = (error) => {
      setState((prev) => ({
        ...prev,
        connectionError: "WebSocket connection error",
      }));
      console.error("🔌 WebSocket error:", error);
    };

    wsRef.current = ws;
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "User initiated disconnect");
      wsRef.current = null;
    }

    setState({
      isConnected: false,
      connectionError: null,
      subscribedEvents: [],
    });
  }, []);

  const handleWebSocketMessage = useCallback(
    (message: WebSocketMessage) => {
      console.log("📨 WebSocket message received:", message.type);

      switch (message.type) {
        case "connection.established":
          console.log("🔌 WebSocket connection established:", message.data);
          break;

        case "subscription.confirmed":
          setState((prev) => ({
            ...prev,
            subscribedEvents: message.data.subscribed_events || [],
          }));
          console.log(
            "✅ Event subscription confirmed:",
            message.data.subscribed_events
          );
          break;

        case "unsubscription.confirmed":
          setState((prev) => ({
            ...prev,
            subscribedEvents: message.data.subscribed_events || [],
          }));
          console.log(
            "✅ Event unsubscription confirmed:",
            message.data.subscribed_events
          );
          break;

        case "trace.created":
          console.log("🆕 Trace created:", message.data);
          queryClient.invalidateQueries({ queryKey: ["rootTraces"] });
          queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
          break;

        case "trace.updated":
          console.log("🔄 Trace updated:", message.data);
          queryClient.invalidateQueries({ queryKey: ["rootTraces"] });
          queryClient.invalidateQueries({ queryKey: ["traceHierarchy"] });
          break;

        case "trace.completed":
          console.log("✅ Trace completed:", message.data);
          queryClient.invalidateQueries({ queryKey: ["rootTraces"] });
          queryClient.invalidateQueries({ queryKey: ["traceHierarchy"] });
          queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
          break;

        case "trace.failed":
          console.log("❌ Trace failed:", message.data);
          queryClient.invalidateQueries({ queryKey: ["rootTraces"] });
          queryClient.invalidateQueries({ queryKey: ["traceHierarchy"] });
          queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
          break;

        case "stats.updated":
          console.log("📊 Stats updated:", message.data);
          queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
          break;

        case "pong":
          console.log("🏓 Pong received:", message.data);
          break;

        case "error":
          console.error("❌ WebSocket error message:", message.data);
          break;

        default:
          console.warn("⚠️ Unknown WebSocket message type:", message.type);
      }
    },
    [queryClient]
  );

  const subscribe = useCallback((events: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        action: "subscribe",
        events,
      };
      wsRef.current.send(JSON.stringify(message));
      console.log("📡 Subscribing to events:", events);
    } else {
      console.warn("⚠️ Cannot subscribe: WebSocket not connected");
    }
  }, []);

  const unsubscribe = useCallback((events: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        action: "unsubscribe",
        events,
      };
      wsRef.current.send(JSON.stringify(message));
      console.log("📡 Unsubscribing from events:", events);
    } else {
      console.warn("⚠️ Cannot unsubscribe: WebSocket not connected");
    }
  }, []);

  const ping = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = { action: "ping" };
      wsRef.current.send(JSON.stringify(message));
      console.log("🏓 Sending ping");
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected: state.isConnected,
    connectionError: state.connectionError,
    subscribedEvents: state.subscribedEvents,
    subscribe,
    unsubscribe,
    ping,
    connect,
    disconnect,
  };
};
