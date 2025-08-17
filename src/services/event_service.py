"""Event service for WebSocket event emission."""

import asyncio
from datetime import datetime
from typing import Any

from src.api.websocket import manager
from src.core.logging import get_logger
from src.models.runs import Run

logger = get_logger(__name__)


class EventService:
    """Service for emitting WebSocket events."""

    @staticmethod
    async def emit_trace_created(run: Run):
        """Emit trace.created event when a new trace is created."""
        try:
            event_data = {
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "project_name": run.project_name,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None
            }

            await manager.broadcast_event("trace.created", event_data)
            logger.debug(f"Emitted trace.created event for run {run.id}")

        except Exception as e:
            logger.error(f"Failed to emit trace.created event for run {run.id}: {e}")

    @staticmethod
    async def emit_trace_updated(run: Run, changes: dict[str, Any]):
        """Emit trace.updated event when a trace is updated."""
        try:
            event_data = {
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "project_name": run.project_name,
                "status": run.status,
                "changes": changes,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None
            }

            await manager.broadcast_event("trace.updated", event_data)
            logger.debug(f"Emitted trace.updated event for run {run.id}")

        except Exception as e:
            logger.error(f"Failed to emit trace.updated event for run {run.id}: {e}")

    @staticmethod
    async def emit_trace_completed(run: Run):
        """Emit trace.completed event when a trace is completed."""
        try:
            event_data = {
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "project_name": run.project_name,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "duration_ms": run.duration_ms if hasattr(run, 'duration_ms') else None,
                "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None
            }

            await manager.broadcast_event("trace.completed", event_data)
            logger.debug(f"Emitted trace.completed event for run {run.id}")

        except Exception as e:
            logger.error(f"Failed to emit trace.completed event for run {run.id}: {e}")

    @staticmethod
    async def emit_trace_failed(run: Run, error_message: str | None = None):
        """Emit trace.failed event when a trace fails."""
        try:
            event_data = {
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "project_name": run.project_name,
                "status": run.status,
                "error": error_message or run.error,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None
            }

            await manager.broadcast_event("trace.failed", event_data)
            logger.debug(f"Emitted trace.failed event for run {run.id}")

        except Exception as e:
            logger.error(f"Failed to emit trace.failed event for run {run.id}: {e}")

    @staticmethod
    async def emit_stats_updated(stats: dict[str, Any]):
        """Emit stats.updated event when dashboard statistics change."""
        try:
            event_data = {
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }

            await manager.broadcast_event("stats.updated", event_data)
            logger.debug("Emitted stats.updated event")

        except Exception as e:
            logger.error(f"Failed to emit stats.updated event: {e}")

    @staticmethod
    async def emit_batch_events(events: list[dict[str, Any]]):
        """Emit multiple events in batch for efficiency."""
        try:
            for event in events:
                event_type = event.get("type")
                event_data = event.get("data", {})

                if event_type == "trace.created":
                    await EventService.emit_trace_created(event_data.get("run"))
                elif event_type == "trace.updated":
                    await EventService.emit_trace_updated(event_data.get("run"), event_data.get("changes", {}))
                elif event_type == "trace.completed":
                    await EventService.emit_trace_completed(event_data.get("run"))
                elif event_type == "trace.failed":
                    await EventService.emit_trace_failed(event_data.get("run"), event_data.get("error"))
                elif event_type == "stats.updated":
                    await EventService.emit_stats_updated(event_data.get("stats", {}))
                else:
                    logger.warning(f"Unknown event type: {event_type}")

            logger.debug(f"Emitted {len(events)} batch events")

        except Exception as e:
            logger.error(f"Failed to emit batch events: {e}")


# Convenience functions for async event emission
async def emit_trace_created_async(run: Run):
    """Async wrapper for trace.created event emission."""
    asyncio.create_task(EventService.emit_trace_created(run))


async def emit_trace_updated_async(run: Run, changes: dict[str, Any]):
    """Async wrapper for trace.updated event emission."""
    asyncio.create_task(EventService.emit_trace_updated(run, changes))


async def emit_trace_completed_async(run: Run):
    """Async wrapper for trace.completed event emission."""
    asyncio.create_task(EventService.emit_trace_completed(run))


async def emit_trace_failed_async(run: Run, error_message: str | None = None):
    """Async wrapper for trace.failed event emission."""
    asyncio.create_task(EventService.emit_trace_failed(run, error_message))


async def emit_stats_updated_async(stats: dict[str, Any]):
    """Async wrapper for stats.updated event emission."""
    asyncio.create_task(EventService.emit_stats_updated(stats))
