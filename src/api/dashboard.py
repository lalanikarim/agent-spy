"""Dashboard-specific endpoints for runs/traces."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.repositories.runs import RunRepository
from src.schemas.dashboard import (
    DashboardStats,
    DashboardSummary,
    ProjectInfo,
    RootRunsResponse,
    RunHierarchyNode,
    RunHierarchyResponse,
)
from src.schemas.runs import RunResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/dashboard/runs/roots",
    response_model=RootRunsResponse,
    summary="Get root traces for dashboard",
)
async def get_root_runs(
    project_name: str | None = Query(None, description="Filter by project name"),
    status: str | None = Query(None, description="Filter by status (running, completed, failed)"),
    search: str | None = Query(None, description="Search in trace names and projects"),
    limit: int = Query(50, description="Maximum number of traces to return", ge=1, le=200),
    offset: int = Query(0, description="Number of traces to skip", ge=0),
    start_time_gte: datetime | None = Query(None, description="Filter by start time (>=)"),
    start_time_lte: datetime | None = Query(None, description="Filter by start time (<=)"),
    db: AsyncSession = Depends(get_db),
) -> RootRunsResponse:
    """Get root traces (parent_run_id = NULL) for dashboard master table."""
    logger.info(f"Getting root runs: project={project_name}, status={status}, search={search}")

    run_repo = RunRepository(db)

    try:
        # Get root runs
        runs = await run_repo.get_root_runs(
            project_name=project_name,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
            start_time_gte=start_time_gte,
            start_time_lte=start_time_lte,
        )

        # Get total count for pagination
        total = await run_repo.count_root_runs(
            project_name=project_name,
            status=status,
            search=search,
            start_time_gte=start_time_gte,
            start_time_lte=start_time_lte,
        )

        has_more = (offset + len(runs)) < total

        return RootRunsResponse(
            runs=[RunResponse.from_run(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )
    except Exception as e:
        logger.error(f"Failed to get root runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get root runs: {e}")


@router.get(
    "/dashboard/runs/{trace_id}/hierarchy",
    response_model=RunHierarchyResponse,
    summary="Get trace hierarchy",
)
async def get_run_hierarchy(trace_id: UUID, db: AsyncSession = Depends(get_db)) -> RunHierarchyResponse:
    """Get complete run hierarchy for a trace (for dashboard detail view)."""
    logger.info(f"Getting hierarchy for trace: {trace_id}")

    run_repo = RunRepository(db)

    try:
        # Get all runs in the hierarchy
        runs = await run_repo.get_run_hierarchy(trace_id)

        if not runs:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

        logger.info(f"API: Repository returned {len(runs)} runs for trace {trace_id}")

        # Build hierarchical structure
        runs_by_id = {run.id: RunHierarchyNode.from_run(run) for run in runs}
        root_node = None
        max_depth = 0

        # First pass: find root and build parent-child relationships
        for run in runs:
            node = runs_by_id[run.id]

            if run.parent_run_id is None:
                # This is the root
                root_node = node
            else:
                # Add to parent's children
                parent_node = runs_by_id.get(run.parent_run_id)
                if parent_node:
                    parent_node.children.append(node)
                else:
                    logger.warning(f"Parent not found for {run.name}: {run.parent_run_id}")

        if not root_node:
            raise HTTPException(status_code=404, detail=f"Root trace {trace_id} not found")

        # Calculate max depth
        def calculate_depth(node: RunHierarchyNode, current_depth: int = 0) -> int:
            max_child_depth = current_depth
            for child in node.children:
                child_depth = calculate_depth(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth

        max_depth = calculate_depth(root_node)

        return RunHierarchyResponse(
            root_run_id=trace_id,
            hierarchy=root_node,
            max_depth=max_depth,
            total_runs=len(runs),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run hierarchy for {trace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get run hierarchy: {e}")


@router.get(
    "/dashboard/stats/summary",
    response_model=DashboardSummary,
    summary="Get dashboard summary",
)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    """Get comprehensive dashboard statistics and summary."""
    logger.info("Getting dashboard summary")

    run_repo = RunRepository(db)

    try:
        # Clean up stale running traces first (configurable timeout)
        from src.core.config import get_settings

        stale_default = get_settings().stale_run_timeout_minutes_default
        stale_count = await run_repo.mark_stale_runs_as_failed(timeout_minutes=stale_default)
        if stale_count > 0:
            logger.info(f"Automatically marked {stale_count} stale traces as failed")
            await db.commit()  # Commit the stale run updates

        # Get dashboard statistics
        stats_data = await run_repo.get_dashboard_stats()
        stats = DashboardStats(**stats_data)

        # Get recent projects (projects with activity in last 7 days)
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)

        recent_runs = await run_repo.list_runs(
            start_time_gte=seven_days_ago,
            limit=1000,  # Get enough to analyze projects
        )

        # Group by project and get stats
        project_stats = {}
        for run in recent_runs:
            project = run.project_name or "Unknown"
            if project not in project_stats:
                project_stats[project] = {
                    "name": project,
                    "total_runs": 0,
                    "total_traces": 0,
                    "last_activity": run.start_time,
                }

            project_stats[project]["total_runs"] += 1
            if run.parent_run_id is None:  # Root run
                project_stats[project]["total_traces"] += 1

            # Update last activity
            if run.start_time > project_stats[project]["last_activity"]:
                project_stats[project]["last_activity"] = run.start_time

        # Convert to ProjectInfo objects and sort by last activity
        recent_projects = [ProjectInfo(**project_data) for project_data in project_stats.values()]
        recent_projects.sort(key=lambda p: p.last_activity or datetime.min, reverse=True)

        return DashboardSummary(
            stats=stats,
            recent_projects=recent_projects[:10],  # Top 10 most recent
            timestamp=datetime.now(UTC),
        )
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {e}")


@router.post("/dashboard/cleanup/stale-runs", summary="Clean up stale running traces")
async def cleanup_stale_runs(
    timeout_minutes: int = Query(30, description="Timeout in minutes for marking traces as failed", ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually trigger cleanup of stale running traces that have exceeded the timeout."""
    logger.info(f"Manual cleanup of stale runs triggered with {timeout_minutes}min timeout")

    run_repo = RunRepository(db)

    try:
        # Mark stale runs as failed
        stale_count = await run_repo.mark_stale_runs_as_failed(timeout_minutes=timeout_minutes)

        if stale_count > 0:
            await db.commit()
            logger.info(f"Successfully marked {stale_count} stale traces as failed")
        else:
            logger.info("No stale traces found to clean up")

        return {
            "success": True,
            "message": "Cleanup completed successfully",
            "stale_runs_marked": stale_count,
            "timeout_minutes": timeout_minutes,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to cleanup stale runs: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cleanup stale runs: {e}")
