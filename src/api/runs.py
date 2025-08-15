"""Runs/traces endpoints for LangSmith compatibility."""

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
from src.schemas.runs import (
    BatchIngestRequest,
    BatchIngestResponse,
    LangSmithInfo,
    RunCreate,
    RunResponse,
    RunUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/info", response_model=LangSmithInfo, summary="Service Information")
async def get_service_info() -> LangSmithInfo:
    """
    Get service information endpoint that LangSmith clients expect.
    
    This endpoint provides information about the service capabilities
    and configuration that LangSmith clients use for compatibility.
    """
    logger.debug("Service info requested")
    
    info = LangSmithInfo(
        version="0.1.0",
        license_expiration_time=None,  # No license expiration for local service
        tenant_handle="agent-spy-local"
    )
    
    logger.info("Service info provided")
    return info


@router.post("/runs/batch", response_model=BatchIngestResponse, summary="Batch Ingest Runs")
async def batch_ingest_runs(
    request: BatchIngestRequest, 
    db: AsyncSession = Depends(get_db)
) -> BatchIngestResponse:
    """
    Batch ingest runs (traces and spans).
    
    This is the main endpoint that LangChain uses to send trace data.
    It accepts both new runs (POST operations) and run updates (PATCH operations).
    """
    logger.info(
        f"🔍 Batch ingest request: {len(request.post)} creates, {len(request.patch)} updates"
    )
    
    # Debug: Log the first few items to see the structure
    if request.post:
        logger.info(f"📝 First POST item: {request.post[0].model_dump()}")
    if request.patch:
        logger.info(f"📝 First PATCH item: {request.patch[0].model_dump()}")
    
    run_repo = RunRepository(db)
    created_count = 0
    updated_count = 0
    errors = 0
    
    # Process new runs (POST operations)
    for run_create in request.post:
        try:
            logger.info(f"🔄 Creating run: {run_create.id}")
            await run_repo.create(run_create)
            created_count += 1
            logger.info(f"✅ Created run: {run_create.id}")
        except Exception as e:
            logger.error(f"❌ Failed to create run {run_create.id}: {e}")
            import traceback
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            errors += 1
    
    # Process run updates (PATCH operations)  
    for run_update in request.patch:
        try:
            updated_run = await run_repo.update(run_update.id, run_update)
            if updated_run:
                updated_count += 1
                logger.debug(f"Updated run: {run_update.id}")
            else:
                logger.warning(f"Run not found for update: {run_update.id}")
                errors += 1
        except Exception as e:
            logger.error(f"Failed to update run {run_update.id}: {e}")
            errors += 1
    
    logger.info(f"Batch ingest completed: created={created_count}, updated={updated_count}, errors={errors}")
    return BatchIngestResponse(
        success=True,
        created_count=created_count,
        updated_count=updated_count,
        errors=[] if errors == 0 else [f"{errors} errors occurred"]
    )


@router.post("/runs", response_model=RunResponse, summary="Create a new run")
async def create_run(
    run_data: RunCreate, 
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
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
async def update_run(
    run_id: UUID, 
    run_data: RunUpdate, 
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
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
    db: AsyncSession = Depends(get_db)
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
async def get_run(
    run_id: UUID, 
    db: AsyncSession = Depends(get_db)
) -> RunResponse:
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
async def add_feedback(
    run_id: UUID, 
    feedback_data: FeedbackCreate, 
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Add feedback to a specific run."""
    logger.info(f"Adding feedback to run: {run_id}")
    
    # First check if the run exists
    run_repo = RunRepository(db)
    run = await run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Create the feedback
    feedback_repo = FeedbackRepository(db)
    
    try:
        feedback = await feedback_repo.create(run_id, feedback_data)
        logger.info(f"Created feedback: {feedback.id} for run: {run_id}")
        
        return {
            "id": str(feedback.id),
            "run_id": str(run_id),
            "score": feedback.score,
            "value": feedback.value,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to add feedback to run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {e}")


@router.get("/stats", summary="Get statistics")
async def get_stats(
    project_name: str | None = Query(None, description="Filter by project name"),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get statistics about runs and feedback."""
    logger.info("Getting statistics")
    
    run_repo = RunRepository(db)
    
    try:
        # Get basic counts
        total_runs = await run_repo.count_runs(project_name=project_name)
        run_types = await run_repo.get_run_types(project_name=project_name)
        
        # Get recent activity (last 10 runs)
        recent_runs = await run_repo.list_runs(
            project_name=project_name,
            limit=10,
            offset=0
        )
        
        recent_activity = []
        for run in recent_runs:
            recent_activity.append({
                "id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "status": run.status,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "project_name": run.project_name,
            })
        
        stats = {
            "total_runs": total_runs,
            "total_feedback": 0,  # TODO: Implement feedback counting
            "run_types": run_types,
            "recent_activity": recent_activity,
        }
        
        logger.info(f"Statistics: {total_runs} runs, {len(run_types)} run types")
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")