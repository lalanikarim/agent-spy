"""Consolidated runs/traces API endpoints.

This file consolidates all run-related endpoints from focused modules:
- runs_crud.py: Basic CRUD operations
- runs_batch.py: Batch processing operations
- runs_dashboard.py: Dashboard-specific endpoints
- runs_langsmith.py: LangSmith compatibility
"""

from fastapi import APIRouter

from .batch import router as batch_router
from .crud import router as crud_router
from .dashboard import router as dashboard_router
from .langsmith import router as langsmith_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(crud_router, tags=["runs-crud"])
router.include_router(batch_router, tags=["runs-batch"])
router.include_router(dashboard_router, tags=["runs-dashboard"])
router.include_router(langsmith_router, tags=["runs-langsmith"])
