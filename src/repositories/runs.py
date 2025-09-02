"""Repository for run data access."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.runs import Run
from src.schemas.runs import RunCreate, RunUpdate
from src.services.event_service import (
    EventService,
)

logger = get_logger(__name__)


class RunRepository:
    """Repository for run data access operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session."""
        self.session = session
        self._deferred_updates = {}  # Initialize deferred updates queue

    async def create(self, run_data: RunCreate, disable_events: bool = False) -> Run:
        """Create a new run."""
        logger.debug(f"Creating run: {run_data.id}")

        # Pattern-based completion detection: if a run arrives with both end_time AND outputs, it's complete
        # This universal pattern works across all run types and is much more reliable than whitelisting
        initial_status = "running"

        if run_data.end_time is not None and run_data.outputs is not None:
            # Universal completion pattern: end_time + outputs = completed (unless there's an error)
            initial_status = "completed" if run_data.error is None else "failed"
            logger.info(f"Auto-completing {run_data.run_type} run '{run_data.name}' with completion data: {run_data.id}")
        elif run_data.end_time is not None and run_data.error is not None:
            # Has end_time but with error = failed
            initial_status = "failed"
            logger.info(f"Marking {run_data.run_type} run '{run_data.name}' as failed: {run_data.id}")
        else:
            # No completion indicators - will be updated via PATCH later
            logger.info(
                f"Creating {run_data.run_type} run '{run_data.name}' in running state, awaiting completion: {run_data.id}"
            )

        run = Run(
            id=run_data.id,
            name=run_data.name,
            run_type=run_data.run_type,
            start_time=run_data.start_time,
            end_time=run_data.end_time,
            parent_run_id=run_data.parent_run_id,
            inputs=run_data.inputs,
            outputs=run_data.outputs,
            extra=run_data.extra,
            serialized=run_data.serialized,
            events=run_data.events,
            tags=run_data.tags,
            project_name=run_data.project_name,
            status=initial_status,
        )

        self.session.add(run)
        await self.session.flush()  # Get the ID without committing

        # Emit WebSocket event for new trace (fire and forget)
        if not disable_events:
            try:
                asyncio.create_task(EventService.emit_trace_created(run))
            except Exception as e:
                logger.warning(f"Failed to emit trace.created event for run {run.id}: {e}")

        logger.info(f"Created run: {run.id}")
        return run

    async def upsert_langsmith_trace(self, trace_data: RunCreate | RunUpdate) -> Run:
        """
        Upsert a LangSmith trace - create if new, update if exists.

        This method handles both RunCreate and RunUpdate data types and provides
        atomic create/update operations to prevent missing outputs in LangSmith traces.
        """
        logger.debug(f"Upserting LangSmith trace: {trace_data.id}")

        # Check if trace exists
        existing_run = await self.get_by_id(trace_data.id)

        if existing_run:
            # Update existing trace
            if isinstance(trace_data, RunUpdate):
                logger.debug(f"Updating existing trace: {trace_data.id}")

                # Validate message sequence before applying update
                if not self.validate_message_sequence(existing_run, trace_data):
                    logger.warning(f"Trace {trace_data.id}: Message sequence validation failed - deferring update")
                    # Queue update for later processing
                    await self.queue_deferred_update(trace_data.id, trace_data, "Message sequence validation failed")
                    # Return existing run with current state
                    return existing_run

                # Apply update and validate status consistency
                updated_run = await self.update(trace_data.id, trace_data)
                if updated_run:
                    self.validate_trace_status_consistency(updated_run)
                    # Try to process any deferred updates now that we have more context
                    await self.process_deferred_updates(trace_data.id)
                return updated_run
            else:
                # Convert RunCreate to RunUpdate for existing trace
                logger.debug(f"Converting RunCreate to RunUpdate for existing trace: {trace_data.id}")

                update_data = RunUpdate(
                    id=trace_data.id,
                    end_time=trace_data.end_time,
                    outputs=trace_data.outputs,
                    error=trace_data.error,
                    extra=trace_data.extra,
                    tags=trace_data.tags,
                    events=trace_data.events,
                )

                # Validate message sequence before applying update
                if not self.validate_message_sequence(existing_run, update_data):
                    logger.warning(f"Trace {trace_data.id}: Message sequence validation failed - deferring update")
                    # Queue update for later processing
                    await self.queue_deferred_update(trace_data.id, update_data, "Message sequence validation failed")
                    return existing_run

                # Apply update and validate status consistency
                updated_run = await self.update(trace_data.id, update_data)
                if updated_run:
                    self.validate_trace_status_consistency(updated_run)
                    # Try to process any deferred updates now that we have more context
                    await self.process_deferred_updates(trace_data.id)
                return updated_run
        else:
            # Create new trace
            if isinstance(trace_data, RunCreate):
                logger.debug(f"Creating new trace: {trace_data.id}")
                return await self.create(trace_data)
            else:
                # Convert RunUpdate to RunCreate for new trace
                logger.debug(f"Converting RunUpdate to RunCreate for new trace: {trace_data.id}")

                # Extract required fields for creation, with sensible defaults
                name = getattr(trace_data, "name", None)
                run_type = getattr(trace_data, "run_type", None)
                start_time = getattr(trace_data, "start_time", None)

                # If essential fields are missing, we need to create them
                if not name:
                    name = f"Trace {trace_data.id}"
                if not run_type:
                    run_type = "chain"  # Default LangSmith run type
                if not start_time:
                    start_time = datetime.now(UTC)

                create_data = RunCreate(
                    id=trace_data.id,
                    name=name,
                    run_type=run_type,
                    start_time=start_time,
                    end_time=trace_data.end_time,
                    outputs=trace_data.outputs,
                    error=trace_data.error,
                    extra=trace_data.extra,
                    tags=trace_data.tags,
                    events=trace_data.events,
                )
                return await self.create(create_data)

    async def update(self, run_id: UUID, run_data: RunUpdate) -> Run | None:
        """Update an existing run."""
        logger.debug(f"Updating run: {run_id}")

        stmt = select(Run).where(Run.id == run_id)
        result = await self.session.execute(stmt)
        logger.debug(f"Found run: {run_id}")
        run = result.scalar_one_or_none()

        if not run:
            logger.warning(f"Run not found for update: {run_id}")
            return None

        # Update fields that are provided
        # Track status changes for event emission
        status_changed = False
        changes = {}

        if run_data.end_time is not None:
            run.end_time = run_data.end_time
            new_status = "completed" if not run_data.error else "failed"
            if run.status != new_status:
                run.status = new_status
                status_changed = True
            changes["end_time"] = run_data.end_time

        if run_data.outputs is not None:
            run.outputs = run_data.outputs
            changes["outputs"] = run_data.outputs

        if run_data.error is not None:
            run.error = run_data.error
            if run.status != "failed":
                run.status = "failed"
                status_changed = True
            changes["error"] = run_data.error

        if run_data.extra is not None:
            # Merge with existing extra data
            if run.extra:
                run.extra.update(run_data.extra)
            else:
                run.extra = run_data.extra

        if run_data.tags is not None:
            run.tags = run_data.tags

        if run_data.events is not None:
            run.events = run_data.events

        if run_data.parent_run_id is not None:
            run.parent_run_id = run_data.parent_run_id

        if run_data.project_name is not None:
            run.project_name = run_data.project_name

        if run_data.reference_example_id is not None:
            run.reference_example_id = run_data.reference_example_id

        await self.session.flush()

        # Emit WebSocket events based on changes (fire and forget)
        if changes:
            try:
                asyncio.create_task(EventService.emit_trace_updated(run, changes))
            except Exception as e:
                logger.warning(f"Failed to emit trace.updated event for run {run.id}: {e}")

        if status_changed:
            if run.status == "completed":
                try:
                    asyncio.create_task(EventService.emit_trace_completed(run))
                except Exception as e:
                    logger.warning(f"Failed to emit trace.completed event for run {run.id}: {e}")
            elif run.status == "failed":
                try:
                    asyncio.create_task(EventService.emit_trace_failed(run, run.error))
                except Exception as e:
                    logger.warning(f"Failed to emit trace.failed event for run {run.id}: {e}")

        logger.info(f"Updated run: {run_id}")
        return run

    def validate_langsmith_completion(self, runs: list[Run]) -> None:
        """
        Validate that completed LangSmith traces have outputs.

        This method checks for traces that are marked as completed but missing outputs,
        which is a common issue with the current separate operations approach.
        """
        for run in runs:
            if run.status == "completed" and not run.outputs:
                logger.warning(f"LangSmith trace {run.id} marked as completed but missing outputs")
                # Revert to running status until outputs are received
                run.status = "running"
                logger.info(f"Reverted trace {run.id} to running status - awaiting outputs")
                # Optionally, queue for retry or alert

    def validate_trace_status_consistency(self, run: Run) -> bool:
        """
        Validate that trace status is consistent with its data.

        This method implements the smart completion detection logic to ensure
        status consistency and prevent premature completion.

        Returns:
            True if status is consistent, False if status needs adjustment
        """
        # Check if we have completion indicators
        has_end_time = run.end_time is not None
        has_outputs = run.outputs is not None
        has_error = run.error is not None

        # Determine expected status based on data
        expected_status = "running"

        if has_error:
            expected_status = "failed"
        elif has_end_time and has_outputs:
            expected_status = "completed"
        elif has_end_time and not has_outputs:
            # Has end_time but no outputs - should remain running until outputs arrive
            expected_status = "running"

        # Check if status needs adjustment
        if run.status != expected_status:
            logger.info(f"Adjusting trace {run.id} status from '{run.status}' to '{expected_status}'")
            logger.info(f"  end_time: {has_end_time}, outputs: {has_outputs}, error: {has_error}")
            run.status = expected_status
            return False

        return True

    def validate_message_sequence(self, run: Run, update_data: RunUpdate) -> bool:
        """
        Validate message sequence to prevent out-of-order updates.

        This method checks if the update makes sense in the context of the current trace state.
        It prevents scenarios like receiving outputs before start_time or end_time before outputs.

        Args:
            run: Current run state
            update_data: Incoming update data

        Returns:
            True if update sequence is valid, False if it should be deferred
        """
        # Check for out-of-order scenarios
        if update_data.end_time and not run.start_time:
            logger.warning(f"Trace {run.id}: Received end_time before start_time - deferring update")
            return False

        if update_data.outputs and not run.start_time:
            logger.warning(f"Trace {run.id}: Received outputs before start_time - deferring update")
            return False

        if update_data.end_time and not update_data.outputs and run.status == "running":
            # This is a valid scenario - trace is ending but outputs will come later
            logger.info(f"Trace {run.id}: Received end_time, awaiting outputs")
            return True

        # Check for premature completion
        if update_data.end_time and update_data.outputs and not self._has_required_fields_for_completion(run, update_data):
            logger.warning(f"Trace {run.id}: Incomplete completion data - deferring update")
            return False

        return True

    def _has_required_fields_for_completion(self, run: Run, update_data: RunUpdate) -> bool:
        """
        Check if we have all required fields for trace completion.

        This method ensures that a trace has all necessary data before being marked as completed.
        """
        # For LangSmith traces, we need at minimum: name, run_type, start_time, end_time, outputs
        required_fields = {
            "name": run.name or getattr(update_data, "name", None),
            "run_type": run.run_type or getattr(update_data, "run_type", None),
            "start_time": run.start_time or getattr(update_data, "start_time", None),
            "end_time": run.end_time or update_data.end_time,
            "outputs": run.outputs or update_data.outputs,
        }

        missing_fields = [field for field, value in required_fields.items() if not value]

        if missing_fields:
            logger.debug(f"Trace {run.id} missing required fields for completion: {missing_fields}")
            return False

        return True

    async def queue_deferred_update(self, run_id: UUID, update_data: RunUpdate, reason: str) -> None:
        """
        Queue a deferred update for later processing.

        This method handles updates that arrive out of order and need to be
        processed later when the trace has the required context.
        """
        logger.info(f"Queueing deferred update for trace {run_id}: {reason}")

        # Store deferred update in memory (could be extended to use Redis/database)
        if not hasattr(self, "_deferred_updates"):
            self._deferred_updates = {}

        if run_id not in self._deferred_updates:
            self._deferred_updates[run_id] = []

        self._deferred_updates[run_id].append({"data": update_data, "reason": reason, "timestamp": datetime.now(UTC)})

        logger.info(f"Queued {len(self._deferred_updates[run_id])} deferred updates for trace {run_id}")

    async def process_deferred_updates(self, run_id: UUID) -> bool:
        """
        Process any deferred updates for a specific trace.

        This method attempts to process previously deferred updates when
        the trace has sufficient context.

        Returns:
            True if updates were processed, False otherwise
        """
        if not hasattr(self, "_deferred_updates") or run_id not in self._deferred_updates:
            return False

        deferred_updates = self._deferred_updates[run_id]
        if not deferred_updates:
            return False

        logger.info(f"Processing {len(deferred_updates)} deferred updates for trace {run_id}")

        # Get current trace state
        current_run = await self.get_by_id(run_id)
        if not current_run:
            logger.warning(f"Trace {run_id} not found for deferred update processing")
            return False

        processed_count = 0
        for update_info in deferred_updates[:]:  # Copy list for iteration
            update_data = update_info["data"]

            # Check if update can now be processed
            if self.validate_message_sequence(current_run, update_data):
                try:
                    logger.info(f"Processing deferred update for trace {run_id}")
                    updated_run = await self.update(run_id, update_data)
                    if updated_run:
                        self.validate_trace_status_consistency(updated_run)
                        processed_count += 1
                        # Remove processed update from queue
                        deferred_updates.remove(update_info)
                        logger.info(f"Successfully processed deferred update for trace {run_id}")
                except Exception as e:
                    logger.error(f"Failed to process deferred update for trace {run_id}: {e}")
            else:
                logger.debug(f"Deferred update for trace {run_id} still not ready: {update_info['reason']}")

        if processed_count > 0:
            logger.info(f"Processed {processed_count} deferred updates for trace {run_id}")
            return True

        return False

    async def get_by_id(self, run_id: UUID) -> Run | None:
        """Get a run by its ID."""
        logger.debug(f"Getting run by ID: {run_id}")

        stmt = select(Run).where(Run.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()

        if run:
            logger.debug(f"Found run: {run_id}")
        else:
            logger.debug(f"Run not found: {run_id}")

        return run

    async def list_runs(
        self,
        project_name: str | None = None,
        run_type: str | None = None,
        parent_run_id: UUID | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
        start_time_gte: datetime | None = None,
        start_time_lte: datetime | None = None,
    ) -> list[Run]:
        """List runs with optional filtering."""
        logger.debug(f"Listing runs with filters: project={project_name}, type={run_type}, limit={limit}")

        stmt = select(Run)

        # Apply filters
        conditions = []

        if project_name is not None:
            conditions.append(Run.project_name == project_name)

        if run_type is not None:
            conditions.append(Run.run_type == run_type)

        if parent_run_id is not None:
            conditions.append(Run.parent_run_id == parent_run_id)

        if status is not None:
            conditions.append(Run.status == status)

        if start_time_gte is not None:
            conditions.append(Run.start_time >= start_time_gte)

        if start_time_lte is not None:
            conditions.append(Run.start_time <= start_time_lte)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order by start_time descending (most recent first)
        stmt = stmt.order_by(desc(Run.start_time))

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        runs = result.scalars().all()

        logger.info(f"Found {len(runs)} runs")
        return list(runs)

    async def get_root_runs(
        self,
        project_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        start_time_gte: datetime | None = None,
        start_time_lte: datetime | None = None,
    ) -> list[Run]:
        """Get root runs (parent_run_id is NULL) for dashboard master table."""
        logger.debug(f"Getting root runs with filters: project={project_name}, status={status}, search={search}")

        stmt = select(Run).where(Run.parent_run_id.is_(None))

        # Apply filters
        conditions = []

        if project_name is not None:
            conditions.append(Run.project_name == project_name)

        if status is not None:
            conditions.append(Run.status == status)

        if search is not None:
            # Search in name and project_name
            search_pattern = f"%{search}%"
            conditions.append((Run.name.ilike(search_pattern)) | (Run.project_name.ilike(search_pattern)))

        if start_time_gte is not None:
            conditions.append(Run.start_time >= start_time_gte)

        if start_time_lte is not None:
            conditions.append(Run.start_time <= start_time_lte)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order by start_time descending (most recent first)
        stmt = stmt.order_by(desc(Run.start_time))

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        runs = result.scalars().all()

        logger.info(f"Found {len(runs)} root runs")
        return list(runs)

    async def count_root_runs(
        self,
        project_name: str | None = None,
        status: str | None = None,
        search: str | None = None,
        start_time_gte: datetime | None = None,
        start_time_lte: datetime | None = None,
    ) -> int:
        """Count root runs with optional filtering."""
        logger.debug("Counting root runs with filters")

        stmt = select(func.count(Run.id)).where(Run.parent_run_id.is_(None))

        # Apply filters
        conditions = []

        if project_name is not None:
            conditions.append(Run.project_name == project_name)

        if status is not None:
            conditions.append(Run.status == status)

        if search is not None:
            search_pattern = f"%{search}%"
            conditions.append((Run.name.ilike(search_pattern)) | (Run.project_name.ilike(search_pattern)))

        if start_time_gte is not None:
            conditions.append(Run.start_time >= start_time_gte)

        if start_time_lte is not None:
            conditions.append(Run.start_time <= start_time_lte)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        count = result.scalar()

        logger.debug(f"Total root runs count: {count}")
        return count or 0

    async def get_run_hierarchy(self, root_run_id: UUID) -> list[Run]:
        """Get complete run hierarchy starting from a root run (recursive)."""
        logger.debug(f"Getting complete hierarchy for root: {root_run_id}")

        # Use a simple recursive approach to get all descendants
        all_runs = []
        visited_ids = set()

        async def collect_descendants(run_id: UUID):
            """Recursively collect all descendants of a run."""
            if run_id in visited_ids:
                return
            visited_ids.add(run_id)

            # Get the run itself
            run_stmt = select(Run).where(Run.id == run_id)
            run_result = await self.session.execute(run_stmt)
            run = run_result.scalar_one_or_none()

            if run:
                all_runs.append(run)

                # Get all direct children
                children_stmt = select(Run).where(Run.parent_run_id == run_id).order_by(Run.start_time)
                children_result = await self.session.execute(children_stmt)
                children = children_result.scalars().all()

                # Recursively collect descendants of each child
                for child in children:
                    await collect_descendants(child.id)

        # Start the recursive collection from the root
        await collect_descendants(root_run_id)

        logger.info(f"Found {len(all_runs)} runs in hierarchy for root {root_run_id}")
        return all_runs

    async def get_run_tree(self, root_run_id: UUID) -> list[Run]:
        """Get a complete run tree starting from a root run (legacy method)."""
        logger.debug(f"Getting run tree for root: {root_run_id}")

        # This is a recursive query to get all descendants
        # For now, we'll use a simple approach and load all related runs
        stmt = select(Run).where((Run.id == root_run_id) | (Run.parent_run_id == root_run_id)).order_by(Run.start_time)

        result = await self.session.execute(stmt)
        runs = result.scalars().all()

        logger.debug(f"Found {len(runs)} runs in tree")
        return list(runs)

    async def count_runs(
        self,
        project_name: str | None = None,
        run_type: str | None = None,
        status: str | None = None,
        start_time_gte: datetime | None = None,
        start_time_lte: datetime | None = None,
    ) -> int:
        """Count runs with optional filtering."""
        logger.debug("Counting runs with filters")

        stmt = select(func.count(Run.id))

        # Apply filters
        conditions = []

        if project_name is not None:
            conditions.append(Run.project_name == project_name)

        if run_type is not None:
            conditions.append(Run.run_type == run_type)

        if status is not None:
            conditions.append(Run.status == status)

        if start_time_gte is not None:
            conditions.append(Run.start_time >= start_time_gte)

        if start_time_lte is not None:
            conditions.append(Run.start_time <= start_time_lte)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        count = result.scalar()

        logger.debug(f"Total runs count: {count}")
        return count or 0

    async def get_run_types(self, project_name: str | None = None) -> dict[str, int]:
        """Get run types and their counts."""
        logger.debug("Getting run type statistics")

        stmt = select(Run.run_type, func.count(Run.id)).group_by(Run.run_type)

        if project_name is not None:
            stmt = stmt.where(Run.project_name == project_name)

        result = await self.session.execute(stmt)
        run_types = dict(result.fetchall())

        logger.debug(f"Run types: {run_types}")
        return run_types

    async def get_recent_runs_by_project(
        self, project_name: str, start_time_gte: str | None = None, limit: int = 50
    ) -> list[Run]:
        """Get recent runs from a specific project."""
        logger.debug(f"Getting recent runs for project: {project_name}")

        stmt = select(Run).where(Run.project_name == project_name)

        if start_time_gte:
            try:
                start_time = datetime.fromisoformat(start_time_gte.replace("Z", "+00:00"))
                stmt = stmt.where(Run.start_time >= start_time)
            except Exception as e:
                logger.warning(f"Invalid start_time_gte format: {start_time_gte}, error: {e}")

        stmt = stmt.order_by(desc(Run.start_time)).limit(limit)

        result = await self.session.execute(stmt)
        runs = result.scalars().all()

        logger.debug(f"Found {len(runs)} recent runs for project {project_name}")
        return list(runs)

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get comprehensive dashboard statistics."""
        logger.debug("Getting dashboard statistics")

        # Total runs
        total_runs_stmt = select(func.count(Run.id))
        total_runs_result = await self.session.execute(total_runs_stmt)
        total_runs = total_runs_result.scalar() or 0

        # Root runs (traces)
        root_runs_stmt = select(func.count(Run.id)).where(Run.parent_run_id.is_(None))
        root_runs_result = await self.session.execute(root_runs_stmt)
        total_traces = root_runs_result.scalar() or 0

        # Status distribution
        status_stmt = select(Run.status, func.count(Run.id)).group_by(Run.status)
        status_result = await self.session.execute(status_stmt)
        status_distribution = dict(status_result.fetchall())

        # Run type distribution
        type_stmt = select(Run.run_type, func.count(Run.id)).group_by(Run.run_type)
        type_result = await self.session.execute(type_stmt)
        run_type_distribution = dict(type_result.fetchall())

        # Project distribution (filter out None project names)
        project_stmt = (
            select(Run.project_name, func.count(Run.id)).where(Run.project_name.is_not(None)).group_by(Run.project_name)
        )
        project_result = await self.session.execute(project_stmt)
        project_distribution = dict(project_result.fetchall())

        # Recent activity (last 24 hours)
        from datetime import timedelta

        twenty_four_hours_ago = datetime.now(UTC) - timedelta(hours=24)
        recent_stmt = select(func.count(Run.id)).where(Run.start_time >= twenty_four_hours_ago)
        recent_result = await self.session.execute(recent_stmt)
        recent_runs = recent_result.scalar() or 0

        stats = {
            "total_runs": total_runs,
            "total_traces": total_traces,
            "recent_runs_24h": recent_runs,
            "status_distribution": status_distribution,
            "run_type_distribution": run_type_distribution,
            "project_distribution": project_distribution,
        }

        logger.info(f"Dashboard stats: {stats}")
        return stats

    async def delete(self, run_id: UUID) -> bool:
        """Delete a run by ID."""
        logger.debug(f"Deleting run: {run_id}")

        stmt = select(Run).where(Run.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            logger.warning(f"Run not found for deletion: {run_id}")
            return False

        await self.session.delete(run)
        await self.session.flush()

        logger.info(f"Deleted run: {run_id}")
        return True

    async def mark_stale_runs_as_failed(self, timeout_minutes: int = 30) -> int:
        """Mark long-running traces as failed if they exceed the timeout.

        Args:
            timeout_minutes: Number of minutes after which a running trace is considered stale

        Returns:
            Number of runs that were marked as failed
        """
        logger.debug(f"Checking for stale runs with timeout: {timeout_minutes} minutes")

        # Calculate the cutoff time
        cutoff_time = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

        # Find running traces that started before the cutoff time
        stmt = select(Run).where(and_(Run.status == "running", Run.start_time < cutoff_time))

        result = await self.session.execute(stmt)
        stale_runs = result.scalars().all()

        if not stale_runs:
            logger.debug("No stale runs found")
            return 0

        # Update all stale runs to failed status
        update_stmt = (
            update(Run)
            .where(and_(Run.status == "running", Run.start_time < cutoff_time))
            .values(
                status="failed",
                error="Trace timed out after 30 minutes - likely process terminated unexpectedly",
                end_time=datetime.now(UTC),
            )
        )

        await self.session.execute(update_stmt)
        await self.session.flush()

        count = len(stale_runs)
        logger.info(f"Marked {count} stale runs as failed (timeout: {timeout_minutes}min)")

        # Log details of marked runs
        for run in stale_runs:
            logger.info(f"Marked as failed: {run.name} (id: {run.id}, started: {run.start_time})")

        return count
