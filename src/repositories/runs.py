"""Repository for run data access."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.logging import get_logger
from src.models.runs import Run
from src.schemas.runs import RunCreate, RunUpdate

logger = get_logger(__name__)


class RunRepository:
    """Repository for run data access operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session."""
        self.session = session
    
    async def create(self, run_data: RunCreate) -> Run:
        """Create a new run."""
        logger.debug(f"Creating run: {run_data.id}")
        
        run = Run(
            id=run_data.id,
            name=run_data.name,
            run_type=run_data.run_type,
            start_time=run_data.start_time,
            parent_run_id=run_data.parent_run_id,
            inputs=run_data.inputs,
            extra=run_data.extra,
            serialized=run_data.serialized,
            events=run_data.events,
            tags=run_data.tags,
            project_name=run_data.project_name,
            status="running",
        )
        
        self.session.add(run)
        await self.session.flush()  # Get the ID without committing
        
        logger.info(f"Created run: {run.id}")
        return run
    
    async def update(self, run_id: UUID, run_data: RunUpdate) -> Run | None:
        """Update an existing run."""
        logger.debug(f"Updating run: {run_id}")
        
        stmt = select(Run).where(Run.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            logger.warning(f"Run not found for update: {run_id}")
            return None
        
        # Update fields that are provided
        if run_data.end_time is not None:
            run.end_time = run_data.end_time
            run.status = "completed" if not run_data.error else "failed"
        
        if run_data.outputs is not None:
            run.outputs = run_data.outputs
        
        if run_data.error is not None:
            run.error = run_data.error
            run.status = "failed"
        
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
        
        if run_data.reference_example_id is not None:
            run.reference_example_id = run_data.reference_example_id
        
        await self.session.flush()
        
        logger.info(f"Updated run: {run_id}")
        return run
    
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
            conditions.append(
                (Run.name.ilike(search_pattern)) | 
                (Run.project_name.ilike(search_pattern))
            )
        
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
            conditions.append(
                (Run.name.ilike(search_pattern)) | 
                (Run.project_name.ilike(search_pattern))
            )
        
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
        
        # First verify the root run exists and is actually a root
        root_stmt = select(Run).where(Run.id == root_run_id)
        root_result = await self.session.execute(root_stmt)
        root_run = root_result.scalar_one_or_none()
        
        if not root_run:
            logger.warning(f"Root run not found: {root_run_id}")
            return []
        
        # Get all runs that belong to this trace hierarchy
        # This uses a recursive approach to find all descendants
        all_runs = []
        runs_to_process = [root_run_id]
        processed_ids = set()
        
        while runs_to_process:
            current_id = runs_to_process.pop(0)
            if current_id in processed_ids:
                continue
            
            # Get current run and its direct children
            stmt = select(Run).where(
                (Run.id == current_id) | (Run.parent_run_id == current_id)
            ).order_by(Run.start_time)
            
            result = await self.session.execute(stmt)
            runs = result.scalars().all()
            
            for run in runs:
                if run.id not in processed_ids:
                    all_runs.append(run)
                    processed_ids.add(run.id)
                    if run.id != current_id:  # Don't re-process the current run
                        runs_to_process.append(run.id)
        
        logger.info(f"Found {len(all_runs)} runs in hierarchy for root {root_run_id}")
        return all_runs

    async def get_run_tree(self, root_run_id: UUID) -> list[Run]:
        """Get a complete run tree starting from a root run (legacy method)."""
        logger.debug(f"Getting run tree for root: {root_run_id}")
        
        # This is a recursive query to get all descendants
        # For now, we'll use a simple approach and load all related runs
        stmt = select(Run).where(
            (Run.id == root_run_id) | (Run.parent_run_id == root_run_id)
        ).order_by(Run.start_time)
        
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
        project_stmt = select(Run.project_name, func.count(Run.id)).where(
            Run.project_name.is_not(None)
        ).group_by(Run.project_name)
        project_result = await self.session.execute(project_stmt)
        project_distribution = dict(project_result.fetchall())
        
        # Recent activity (last 24 hours)
        from datetime import timedelta
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
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

