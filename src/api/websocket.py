"""WebSocket API for real-time updates."""

import json
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.core.logging import get_logger

# Get settings and logger
settings = get_settings()
logger = get_logger(__name__)

# Create router
router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections and event broadcasting."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[str]] = {}  # client_id -> event_types
        self.client_metadata: dict[str, dict[str, Any]] = {}  # client_id -> metadata

    async def connect(self, websocket: WebSocket, client_id: str, metadata: dict[str, Any] | None = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
        self.client_metadata[client_id] = metadata or {}

        logger.info(f"WebSocket client {client_id} connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]

        logger.info(f"WebSocket client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_event(self, event_type: str, data: dict, filter_func: Callable | None = None):
        """Broadcast an event to all subscribed clients."""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        message_json = json.dumps(message)
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            # Check if client is subscribed to this event type
            if event_type not in self.subscriptions.get(client_id, set()):
                continue

            # Apply custom filter if provided
            if filter_func and not filter_func(client_id, self.client_metadata.get(client_id, {})):
                continue

            try:
                await websocket.send_text(message_json)
                logger.debug(f"Sent {event_type} event to client {client_id}")
            except Exception as e:
                logger.error(f"Failed to send event to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def send_to_client(self, client_id: str, event_type: str, data: dict):
        """Send an event to a specific client."""
        if client_id not in self.active_connections:
            logger.warning(f"Attempted to send event to non-existent client {client_id}")
            return

        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await self.active_connections[client_id].send_text(json.dumps(message))
            logger.debug(f"Sent {event_type} event to client {client_id}")
        except Exception as e:
            logger.error(f"Failed to send event to client {client_id}: {e}")
            await self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_client_subscriptions(self, client_id: str) -> set[str]:
        """Get the event types a client is subscribed to."""
        return self.subscriptions.get(client_id, set()).copy()

    def get_client_metadata(self, client_id: str) -> dict[str, Any]:
        """Get metadata for a specific client."""
        return self.client_metadata.get(client_id, {}).copy()


# Global WebSocket manager instance
manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    client_id = str(uuid.uuid4())

    try:
        await manager.connect(websocket, client_id)

        # Send welcome message
        await manager.send_to_client(client_id, "connection.established", {
            "client_id": client_id,
            "message": "WebSocket connection established",
            "supported_events": [
                "trace.created",
                "trace.updated",
                "trace.completed",
                "trace.failed",
                "stats.updated"
            ]
        })

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("action") == "subscribe":
                    events = message.get("events", [])
                    manager.subscriptions[client_id].update(events)
                    logger.info(f"Client {client_id} subscribed to events: {events}")

                    # Send confirmation
                    await manager.send_to_client(client_id, "subscription.confirmed", {
                        "subscribed_events": list(manager.subscriptions[client_id])
                    })

                elif message.get("action") == "unsubscribe":
                    events = message.get("events", [])
                    manager.subscriptions[client_id].difference_update(events)
                    logger.info(f"Client {client_id} unsubscribed from events: {events}")

                    # Send confirmation
                    await manager.send_to_client(client_id, "unsubscription.confirmed", {
                        "subscribed_events": list(manager.subscriptions[client_id])
                    })

                elif message.get("action") == "ping":
                    # Handle ping for connection health
                    await manager.send_to_client(client_id, "pong", {
                        "timestamp": datetime.utcnow().isoformat()
                    })

                else:
                    logger.warning(f"Unknown action from client {client_id}: {message.get('action')}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}")
                await manager.send_to_client(client_id, "error", {
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error handling WebSocket connection for client {client_id}: {e}")
    finally:
        await manager.disconnect(client_id)


@router.get("/ws/health")
async def websocket_health():
    """Health check endpoint for WebSocket service."""
    return JSONResponse({
        "status": "healthy",
        "active_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat()
    })


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    stats = {
        "active_connections": manager.get_connection_count(),
        "total_subscriptions": sum(len(subs) for subs in manager.subscriptions.values()),
        "clients": []
    }

    for client_id in manager.active_connections:
        stats["clients"].append({
            "client_id": client_id,
            "subscriptions": list(manager.get_client_subscriptions(client_id)),
            "metadata": manager.get_client_metadata(client_id)
        })

    return JSONResponse(stats)
