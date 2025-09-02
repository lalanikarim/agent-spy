"""Basic CRUD operations for runs/traces."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.repositories.feedback import FeedbackRepository
from src.repositories.runs import RunRepository
from src.schemas.feedback import FeedbackCreate
from src.schemas.runs import RunCreate, RunResponse, RunUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.post("/runs", response_model=RunResponse, summary="Create a new run")
async def create_run(run_data: RunCreate, db: AsyncSession = Depends(get_db)) -> RunResponse:
    """Create a new run (trace or span)."""
    logger.info(f"Creating run: {run_data.id} - {run_data.name}")

    run_repo = RunRepository(db)

    try:
        run = await run_repo.create(run_data)
        return RunResponse.from_run(run)
    except Exception as e:
        logger.error(f"Failed to create run {run_data.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create run: {e}")


@router.patch("/runs/{run_id}", response_model=RunResponse, summary="Update an existing run")
async def update_run(run_id: UUID, run_data: RunUpdate, db: AsyncSession = Depends(get_db)) -> RunResponse:
    """Update an existing run (trace or span)."""
    logger.info(f"Updating run: {run_id}")

    run_repo = RunRepository(db)

    try:
        run = await run_repo.update(run_id, run_data)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        return RunResponse.from_run(run)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update run: {e}")


@router.get("/runs", response_model=list[RunResponse], summary="List runs")
async def list_runs(
    project_name: str | None = Query(None, description="Filter by project name"),
    run_type: str | None = Query(None, description="Filter by run type"),
    parent_run_id: UUID | None = Query(None, description="Filter by parent run ID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of runs to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of runs to skip", ge=0),
    start_time_gte: datetime | None = Query(None, description="Filter by start time (>=)"),
    start_time_lte: datetime | None = Query(None, description="Filter by start time (<=)"),
    db: AsyncSession = Depends(get_db),
) -> list[RunResponse]:
    """List runs with optional filtering and pagination."""
    logger.info(f"Listing runs with filters: project={project_name}, type={run_type}, limit={limit}")

    run_repo = RunRepository(db)

    try:
        runs = await run_repo.list_runs(
            project_name=project_name,
            run_type=run_type,
            parent_run_id=parent_run_id,
            status=status,
            limit=limit,
            offset=offset,
            start_time_gte=start_time_gte,
            start_time_lte=start_time_lte,
        )

        return [RunResponse.from_run(run) for run in runs]
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {e}")


@router.get("/runs/{run_id}", response_model=RunResponse, summary="Get a specific run")
async def get_run(run_id: UUID, db: AsyncSession = Depends(get_db)) -> RunResponse:
    """Get details for a specific run (trace or span)."""
    logger.info(f"Getting run: {run_id}")

    run_repo = RunRepository(db)

    try:
        run = await run_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        return RunResponse.from_run(run)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get run: {e}")


@router.post("/runs/{run_id}/feedback", summary="Add feedback to a run")
async def add_feedback(run_id: UUID, feedback_data: FeedbackCreate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Add feedback to a specific run."""
    logger.info(f"Adding feedback to run: {run_id}")

    feedback_repo = FeedbackRepository(db)

    try:
        feedback = await feedback_repo.create(feedback_data)
        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "message": "Feedback added successfully",
        }
    except Exception as e:
        logger.error(f"Failed to add feedback to run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {e}")


@router.get("/stats", summary="Get statistics")
async def get_stats(
    project_name: str | None = Query(None, description="Filter by project name"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get basic statistics about runs."""
    logger.info(f"Getting stats for project: {project_name}")

    run_repo = RunRepository(db)

    try:
        # Get basic counts
        total_runs = await run_repo.count_runs(project_name=project_name)
        completed_runs = await run_repo.count_runs(project_name=project_name, status="completed")
        failed_runs = await run_repo.count_runs(project_name=project_name, status="failed")
        running_runs = await run_repo.count_runs(project_name=project_name, status="running")

        # Get run type distribution
        run_types = await run_repo.get_run_type_distribution(project_name=project_name)

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "run_types": run_types,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")
