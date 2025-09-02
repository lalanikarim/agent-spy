"""Runs/traces endpoints for LangSmith compatibility and dashboard."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_db
from src.core.logging import get_logger
from src.otel.forwarder import OtlpForwarderConfig, OtlpForwarderService
from src.repositories.feedback import FeedbackRepository
from src.repositories.runs import RunRepository
from src.schemas.dashboard import (
    DashboardStats,
    DashboardSummary,
    ProjectInfo,
    RootRunsResponse,
    RunHierarchyNode,
    RunHierarchyResponse,
)
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

# Initialize OTLP forwarder service
settings = get_settings()
forwarder_config = OtlpForwarderConfig(
    enabled=settings.otlp_forwarder_enabled,
    endpoint=settings.otlp_forwarder_endpoint,
    protocol=settings.otlp_forwarder_protocol,
    service_name=settings.otlp_forwarder_service_name,
    timeout=settings.otlp_forwarder_timeout,
    retry_count=settings.otlp_forwarder_retry_count,
    headers=settings.otlp_forwarder_headers,
)
forwarder_service = OtlpForwarderService(forwarder_config)


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
        tenant_handle="agent-spy-local",
    )

    logger.info("Service info provided")
    return info


@router.post("/runs/batch", response_model=BatchIngestResponse, summary="Batch Ingest Runs")
async def batch_ingest_runs(
    request: BatchIngestRequest, db: AsyncSession = Depends(get_db), http_request: Request = None
) -> BatchIngestResponse:
    """
    Batch ingest runs (traces and spans).

    This is the main endpoint that LangChain uses to send trace data.
    It accepts both new runs (POST operations) and run updates (PATCH operations).
    """
    logger.info(f"🔍 Batch ingest request: {len(request.post)} creates, {len(request.patch)} updates")

    # Debug: Log headers to check for project name
    if http_request:
        logger.info("📋 Request headers:")
        for header_name, header_value in http_request.headers.items():
            if "project" in header_name.lower() or "langsmith" in header_name.lower():
                logger.info(f"  {header_name}: {header_value}")

        # Check common header names for project
        project_headers = ["x-langsmith-project", "langsmith-project", "project", "x-project"]
        for header in project_headers:
            value = http_request.headers.get(header)
            if value:
                logger.info(f"🎯 Found project in header {header}: {value}")

    # Debug: Log the first few items to see the structure
    debug_info = {}
    if request.post:
        first_item = request.post[0]
        debug_info["first_post_item"] = first_item.model_dump()
        logger.info(f"📝 First POST item full dump: {first_item.model_dump()}")

        # Check if metadata contains project info
        if hasattr(first_item, "extra") and first_item.extra:
            debug_info["extra_structure"] = first_item.extra
            logger.info(f"📋 Extra data structure: {json.dumps(first_item.extra, indent=2, default=str)}")
        else:
            debug_info["extra_structure"] = None
            logger.info("📋 No extra data found or extra is empty")
    if request.patch:
        logger.info(f"📝 First PATCH item: {request.patch[0].model_dump()}")

    run_repo = RunRepository(db)
    created_count = 0
    updated_count = 0
    errors = 0
    created_runs = []  # Track created runs for forwarding
    updated_runs = []  # Track updated runs for forwarding

    # Extract project name from headers or metadata if not in request body
    project_from_headers = None
    project_from_metadata = None

    if http_request:
        project_headers = ["x-langsmith-project", "langsmith-project", "project", "x-project"]
        for header in project_headers:
            value = http_request.headers.get(header)
            if value:
                project_from_headers = value
                logger.info(f"🎯 Using project from header {header}: {value}")
                break

    # Check first item's metadata for project name (from either POST or PATCH)
    logger.info("🔍 Starting metadata extraction...")
    first_item = None
    if request.post and len(request.post) > 0:
        first_item = request.post[0]
        logger.info("🔍 Using POST item for metadata extraction")
    elif request.patch and len(request.patch) > 0:
        first_item = request.patch[0]
        logger.info("🔍 Using PATCH item for metadata extraction")

    if first_item and hasattr(first_item, "extra") and first_item.extra:
        # Look for project name in metadata structure: extra.metadata.LANGSMITH_PROJECT
        extra = first_item.extra
        logger.info(f"📋 Extra data keys: {list(extra.keys()) if extra else 'no extra data'}")

        if extra and "metadata" in extra:
            metadata = extra["metadata"]
            logger.info(f"📋 Metadata keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'not a dict'}")

            if isinstance(metadata, dict):
                logger.info(f"🔍 Checking metadata dict with keys: {list(metadata.keys())}")
                # Check for LANGSMITH_PROJECT in metadata
                if "LANGSMITH_PROJECT" in metadata:
                    project_from_metadata = metadata["LANGSMITH_PROJECT"]
                    logger.info(f"🎯 Found project in metadata.LANGSMITH_PROJECT: {project_from_metadata}")
                # Fallback to other possible keys
                elif "project" in metadata:
                    project_from_metadata = metadata["project"]
                    logger.info(f"🎯 Found project in metadata.project: {project_from_metadata}")
                elif "project_name" in metadata:
                    project_from_metadata = metadata["project_name"]
                    logger.info(f"🎯 Found project in metadata.project_name: {project_from_metadata}")
                else:
                    logger.info(f"❌ No project found in metadata keys: {list(metadata.keys())}")

        # Also check for direct project keys in extra (fallback)
        elif extra:
            if "project" in extra:
                project_from_metadata = extra["project"]
                logger.info(f"🎯 Found project in extra.project: {project_from_metadata}")
            elif "LANGSMITH_PROJECT" in extra:
                project_from_metadata = extra["LANGSMITH_PROJECT"]
                logger.info(f"🎯 Found project in extra.LANGSMITH_PROJECT: {project_from_metadata}")

    # Process all operations atomically using upserts with batch transaction (Phase 3.1)
    logger.info(f"🔄 Processing {len(request.post)} POST and {len(request.patch)} PATCH operations atomically")

    # Phase 3.1: Implement Batch Transactions - Wrap entire operation in database transaction
    async with db.begin_nested() as nested_transaction:  # Savepoint for rollback
        try:
            # Combine all operations into a single upsert batch
            all_operations = []

            # Add POST operations (trace creation)
            for run_create in request.post:
                # Apply project name extraction
                if not run_create.project_name:
                    if project_from_metadata:
                        run_create.project_name = project_from_metadata
                        logger.info(f"📝 Set project_name from metadata: {project_from_metadata}")
                    elif project_from_headers:
                        run_create.project_name = project_from_headers
                        logger.info(f"📝 Set project_name from headers: {project_from_headers}")
                    else:
                        logger.info("❌ No project source available")
                else:
                    logger.info(f"📝 Project already set in run_create: {run_create.project_name}")

                all_operations.append(("create", run_create))
                logger.info(f"🔄 Queued POST operation: {run_create.id} (project: {run_create.project_name})")

            # Add PATCH operations (trace updates)
            for run_update in request.patch:
                # Apply project name extraction to PATCH operations too
                current_project = getattr(run_update, "project_name", None)
                if not current_project:
                    if project_from_metadata:
                        run_update.project_name = project_from_metadata
                        logger.info(f"📝 Set project_name from metadata on PATCH: {project_from_metadata}")
                    elif project_from_headers:
                        run_update.project_name = project_from_headers
                        logger.info(f"📝 Set project_name from headers on PATCH: {project_from_headers}")
                    else:
                        logger.info("❌ No project source available for PATCH - will preserve existing project_name")
                else:
                    logger.info(f"📝 Project already set in run_update: {current_project}")

                all_operations.append(("update", run_update))
                project_name = getattr(run_update, "project_name", None)
                logger.info(f"🔄 Queued PATCH operation: {run_update.id} (project: {project_name})")

            # Process all operations atomically using upserts
            logger.info(f"🔄 Processing {len(all_operations)} operations atomically")

            # Phase 3.3: Improve Batch Validation - Pre-validate entire batch before processing
            logger.info("🔍 Pre-validating batch operations...")
            validation_errors = []

            for op_type, trace_data in all_operations:
                # Validate required fields for each operation
                if op_type == "create":
                    missing_fields = []
                    if not trace_data.name:
                        missing_fields.append("name")
                    if not trace_data.run_type:
                        missing_fields.append("run_type")
                    if not trace_data.start_time:
                        missing_fields.append("start_time")

                    if missing_fields:
                        validation_errors.append(f"POST operation {trace_data.id}: Missing required fields {missing_fields}")
                elif op_type == "update":
                    if not trace_data.id:
                        validation_errors.append("PATCH operation: Missing trace ID")

            if validation_errors:
                logger.error(f"❌ Batch validation failed: {len(validation_errors)} errors")
                for error in validation_errors:
                    logger.error(f"   - {error}")

                # Rollback transaction due to validation failures
                await nested_transaction.rollback()
                logger.info("🔄 Batch transaction rolled back due to validation failures")

                return BatchIngestResponse(success=False, created_count=0, updated_count=0, errors=validation_errors)

            logger.info("✅ Batch validation passed - proceeding with processing")

            # Phase 3.2: Add Partial Success Handling - Track failures and implement rollback logic
            failed_operations = []

            for op_type, trace_data in all_operations:
                try:
                    if op_type == "create":
                        logger.info(f"🔄 Upserting POST operation: {trace_data.id}")
                        result = await run_repo.upsert_langsmith_trace(trace_data)
                        created_count += 1
                        created_runs.append(result)
                        logger.info(f"✅ Successfully upserted POST operation: {trace_data.id}")
                    else:  # update
                        logger.info(f"🔄 Upserting PATCH operation: {trace_data.id}")
                        result = await run_repo.upsert_langsmith_trace(trace_data)
                        updated_count += 1
                        updated_runs.append(result)
                        logger.info(f"✅ Successfully upserted PATCH operation: {trace_data.id}")

                except Exception as e:
                    logger.error(f"❌ Failed to upsert {op_type} operation {trace_data.id}: {e}")
                    import traceback

                    logger.error(f"📍 Traceback: {traceback.format_exc()}")
                    errors += 1
                    failed_operations.append((op_type, trace_data, str(e)))

                    # Phase 3.2: Implement rollback on partial failures for critical operations
                    if errors > 0 and len(failed_operations) > 0:
                        logger.warning(f"⚠️ Partial failure detected: {errors} errors out of {len(all_operations)} operations")

                        # For LangSmith traces, even one failure can cause missing outputs
                        # Implement rollback to maintain consistency
                        if any(op_type == "update" for op_type, _, _ in failed_operations):
                            logger.error("🚨 Critical failure: Update operations failed - rolling back entire batch")
                            await nested_transaction.rollback()
                            logger.info("🔄 Batch transaction rolled back due to critical failures")

                            return BatchIngestResponse(
                                success=False,
                                created_count=0,
                                updated_count=0,
                                errors=[
                                    f"Critical failures detected: {len(failed_operations)} operations failed. "
                                    + "Batch rolled back for consistency."
                                ],
                            )

            # Validate completion and status consistency for all processed traces
            if created_runs or updated_runs:
                trace_count = len(created_runs) + len(updated_runs)
                logger.info(f"🔍 Validating completion and status consistency for {trace_count} traces")

                # Validate basic completion (outputs present)
                run_repo.validate_langsmith_completion(created_runs + updated_runs)

                # Validate status consistency for each trace
                for run in created_runs + updated_runs:
                    run_repo.validate_trace_status_consistency(run)
                    logger.debug(f"Validated trace {run.id}: status={run.status}, has_outputs={bool(run.outputs)}")

            logger.info(
                f"✅ Atomic upsert processing completed: {created_count} created, {updated_count} updated, {errors} errors"
            )

            # Process any remaining deferred updates for all traces
            if created_runs or updated_runs:
                logger.info("🔄 Processing any remaining deferred updates...")
                deferred_processed = 0
                for run in created_runs + updated_runs:
                    try:
                        if await run_repo.process_deferred_updates(run.id):
                            deferred_processed += 1
                    except Exception as e:
                        logger.warning(f"Failed to process deferred updates for trace {run.id}: {e}")

                if deferred_processed > 0:
                    logger.info(f"✅ Processed {deferred_processed} deferred updates")
                else:
                    logger.info("ℹ️ No deferred updates to process")

            # Phase 3.1: Commit the batch transaction if all operations succeeded
            logger.info("✅ Batch transaction completed successfully - committing changes")

        except Exception as e:
            # Phase 3.1: Rollback batch transaction on critical errors
            logger.error(f"❌ Critical error in batch transaction - rolling back: {e}")
            await nested_transaction.rollback()
            logger.info("🔄 Batch transaction rolled back successfully")

            # Don't continue with forwarding if critical error occurred
            return BatchIngestResponse(
                success=False, created_count=0, updated_count=0, errors=[f"Critical error in batch processing: {str(e)}"]
            )

    # Forward runs to OTLP endpoint if enabled
    runs_to_forward = created_runs + updated_runs

    # For LangGraph workflows, also forward related traces in the same project
    if forwarder_service and runs_to_forward:
        try:
            # Get project names from the runs being processed
            project_names = set()
            for run in runs_to_forward:
                if run.project_name:
                    project_names.add(run.project_name)

            # If we have project names, also forward recent traces from the same projects
            if project_names:
                logger.info(f"🔍 Looking for related traces in projects: {project_names}")

                # Get recent traces from the same projects (last 5 minutes)
                from datetime import datetime, timedelta

                recent_time = (datetime.now() - timedelta(minutes=5)).isoformat()

                for project_name in project_names:
                    try:
                        # Get recent traces from this project
                        recent_traces = await run_repo.get_recent_runs_by_project(
                            project_name=project_name, start_time_gte=recent_time, limit=50
                        )

                        if recent_traces:
                            # Add recent traces that aren't already in our list
                            existing_ids = {run.id for run in runs_to_forward}
                            for recent_run in recent_traces:
                                if recent_run.id not in existing_ids:
                                    runs_to_forward.append(recent_run)

                            logger.info(f"📋 Added {len(recent_traces)} recent traces from project '{project_name}'")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not fetch recent traces for project '{project_name}': {e}")

            logger.info(f"🔄 Forwarding {len(runs_to_forward)} runs to OTLP endpoint")
            logger.info(f"📋 Runs to forward: {[run.id for run in runs_to_forward]}")
            await forwarder_service.forward_runs(runs_to_forward)
            logger.info(f"✅ Successfully queued {len(runs_to_forward)} runs for OTLP forwarding")
        except Exception as e:
            logger.error(f"❌ Error forwarding runs to OTLP: {e}")
            # Don't fail the main request if forwarding fails
    else:
        logger.info(f"ℹ️ No runs to forward: forwarder_enabled={bool(forwarder_service)}, runs_count={len(runs_to_forward)}")

    logger.info(f"Batch ingest completed: created={created_count}, updated={updated_count}, errors={errors}")
    return BatchIngestResponse(
        success=True,
        created_count=created_count,
        updated_count=updated_count,
        errors=[] if errors == 0 else [f"{errors} errors occurred"],
    )


@router.post("/runs", response_model=RunResponse, summary="Create a new run")
async def create_run(run_data: RunCreate, db: AsyncSession = Depends(get_db)) -> RunResponse:
    """Create a new run (trace or span)."""
    logger.info(f"Creating run: {run_data.id} - {run_data.name}")

    run_repo = RunRepository(db)

    try:
        run = await run_repo.create(run_data)

        # Forward run to OTLP endpoint if enabled
        if forwarder_service:
            try:
                logger.info(f"🔄 Forwarding individual run {run.id} to OTLP endpoint")
                await forwarder_service.forward_runs([run])
                logger.info(f"✅ Successfully queued individual run {run.id} for OTLP forwarding")
            except Exception as e:
                logger.error(f"❌ Error forwarding individual run {run.id} to OTLP: {e}")
                # Don't fail the main request if forwarding fails

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

        # Forward updated run to OTLP endpoint if enabled
        if forwarder_service and run:
            try:
                logger.info(f"🔄 Forwarding updated run {run.id} to OTLP endpoint")
                await forwarder_service.forward_runs([run])
                logger.info(f"✅ Successfully queued updated run {run.id} for OTLP forwarding")
            except Exception as e:
                logger.error(f"❌ Error forwarding updated run {run.id} to OTLP: {e}")
                # Don't fail the main request if forwarding fails

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
            "created_at": feedback.created_at.astimezone().replace(tzinfo=None).isoformat() if feedback.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to add feedback to run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {e}")


@router.get("/stats", summary="Get statistics")
async def get_stats(
    project_name: str | None = Query(None, description="Filter by project name"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get statistics about runs and feedback."""
    logger.info("Getting statistics")

    run_repo = RunRepository(db)

    try:
        # Get basic counts
        total_runs = await run_repo.count_runs(project_name=project_name)
        run_types = await run_repo.get_run_types(project_name=project_name)

        # Get recent activity (last 10 runs)
        recent_runs = await run_repo.list_runs(project_name=project_name, limit=10, offset=0)

        recent_activity = []
        for run in recent_runs:
            recent_activity.append(
                {
                    "id": str(run.id),
                    "name": run.name,
                    "run_type": run.run_type,
                    "status": run.status,
                    "start_time": run.start_time.astimezone().replace(tzinfo=None).isoformat() if run.start_time else None,
                    "project_name": run.project_name,
                }
            )

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


# ================================
# Dashboard-specific endpoints
# ================================


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
            total_runs=len(runs),
            max_depth=max_depth + 1,  # +1 because depth starts at 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hierarchy for trace {trace_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trace hierarchy: {e}")


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
        # Clean up stale running traces first (30-minute timeout)
        stale_count = await run_repo.mark_stale_runs_as_failed(timeout_minutes=30)
        if stale_count > 0:
            logger.info(f"Automatically marked {stale_count} stale traces as failed")
            await db.commit()  # Commit the stale run updates

        # Get dashboard statistics
        stats_data = await run_repo.get_dashboard_stats()
        stats = DashboardStats(**stats_data)

        # Get recent projects (projects with activity in last 7 days)
        from datetime import timedelta

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
