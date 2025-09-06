"""Batch processing operations for runs/traces."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.repositories.runs import RunRepository
from src.schemas.runs import BatchIngestRequest, BatchIngestResponse

logger = get_logger(__name__)
router = APIRouter()


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

    # Project mapping policy: always use session_name as project_name
    session_project = None
    from contextlib import suppress

    with suppress(Exception):
        if request.post and getattr(request.post[0], "session_name", None):
            session_project = request.post[0].session_name
            logger.info(f"🎯 Using project from session_name: {session_project}")

    for item in list(request.post or []):
        with suppress(Exception):
            item.project_name = session_project
    for item in list(request.patch or []):
        with suppress(Exception):
            item.project_name = session_project

    # Debug: Log the first few items to see the structure
    debug_info = {}
    if request.post:
        first_item = request.post[0]
        debug_info["first_post_item"] = first_item.model_dump()
        # Only log shallow keys to avoid very large logs
        shallow = {}
        for k, v in first_item.model_dump().items():
            if k in {"id", "name", "run_type", "project_name"}:
                shallow[k] = v
            else:
                shallow[k] = type(v).__name__
        logger.info(f"PROJECT_POST_ITEM {shallow}")

        # Check if metadata contains project info
        if hasattr(first_item, "extra") and first_item.extra:
            debug_info["extra_structure"] = first_item.extra
            logger.info(f"🔍 Extra metadata structure: {first_item.extra}")

    run_repo = RunRepository(db)
    created_runs = []
    updated_runs = []
    errors = []

    try:
        # Process POST operations (create new runs)
        if request.post:
            logger.info(f"🔄 Processing {len(request.post)} POST operations")
            for i, run_data in enumerate(request.post):
                try:
                    # Use LangSmith-specific upsert logic for better trace handling
                    if hasattr(run_repo, "upsert_langsmith_trace"):
                        # Use the specialized LangSmith trace processing
                        created_run = await run_repo.upsert_langsmith_trace(run_data)
                        if created_run:
                            created_runs.append(created_run)
                            logger.debug(f"✅ LangSmith trace processed {run_data.id} ({i + 1}/{len(request.post)})")
                    else:
                        # Fallback to basic create logic
                        existing_run = await run_repo.get_by_id(run_data.id)
                        if existing_run:
                            logger.warning(f"Run {run_data.id} already exists, skipping creation")
                            continue

                        created_run = await run_repo.create(run_data, disable_events=True)
                        created_runs.append(created_run)
                        logger.debug(f"✅ Created run {run_data.id} ({i + 1}/{len(request.post)})")

                except Exception as e:
                    error_msg = f"Failed to create run {run_data.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Process PATCH operations (update existing runs)
        if request.patch:
            logger.info(f"🔄 Processing {len(request.patch)} PATCH operations")
            for i, run_data in enumerate(request.patch):
                try:
                    # Use LangSmith-specific upsert logic for better trace handling
                    if hasattr(run_repo, "upsert_langsmith_trace"):
                        # Use the specialized LangSmith trace processing for updates
                        updated_run = await run_repo.upsert_langsmith_trace(run_data)
                        if updated_run:
                            updated_runs.append(updated_run)
                            logger.debug(f"✅ LangSmith trace updated {run_data.id} ({i + 1}/{len(request.patch)})")
                        else:
                            error_msg = f"Run {run_data.id} not found for update"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                    else:
                        # Fallback to basic update logic
                        updated_run = await run_repo.update(run_data.id, run_data, disable_events=True)
                        if updated_run:
                            updated_runs.append(updated_run)
                            logger.debug(f"✅ Updated run {run_data.id} ({i + 1}/{len(request.patch)})")
                        else:
                            error_msg = f"Run {run_data.id} not found for update"
                            logger.warning(error_msg)
                            errors.append(error_msg)

                except Exception as e:
                    error_msg = f"Failed to update run {run_data.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Commit all changes
        await db.commit()

        # Forward to OTLP endpoints (fire and forget). Send as one combined batch
        # so the forwarder can group parent/child runs into a single hierarchical trace.
        try:
            from src.core.otlp_forwarder import get_otlp_forwarder

            otlp_forwarder = get_otlp_forwarder()
            if otlp_forwarder and otlp_forwarder.tracer:
                combined: list = []
                if created_runs:
                    combined.extend(created_runs)
                if updated_runs:
                    combined.extend(updated_runs)
                if combined:
                    asyncio.create_task(otlp_forwarder.forward_runs(combined))
                    logger.debug(
                        "OTLP forwarding initiated for combined batch: %s created, %s updated",
                        len(created_runs),
                        len(updated_runs),
                    )
        except Exception as e:
            logger.warning(f"Failed to forward batch traces to OTLP endpoints: {e}")

        # Log summary
        logger.info(
            f"🎉 Batch ingest completed: {len(created_runs)} created, {len(updated_runs)} updated, {len(errors)} errors"
        )

        return BatchIngestResponse(
            success=len(errors) == 0,
            created_count=len(created_runs),
            updated_count=len(updated_runs),
            errors=[] if len(errors) == 0 else [f"{len(errors)} errors occurred"],
        )

    except Exception as e:
        logger.error(f"❌ Batch ingest failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Batch ingest failed: {e}")
