"""Dashboard-specific schemas for API responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.runs import RunResponse


class RootRunsResponse(BaseModel):
    """Response model for root runs listing."""

    runs: list[RunResponse] = Field(description="List of root runs")
    total: int = Field(description="Total number of root runs matching filters")
    limit: int = Field(description="Limit used for pagination")
    offset: int = Field(description="Offset used for pagination")
    has_more: bool = Field(description="Whether there are more runs available")


class RunHierarchyNode(BaseModel):
    """Single node in a run hierarchy."""

    id: UUID
    name: str
    run_type: str
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    parent_run_id: UUID | None = None
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    error: str | None = None
    extra: dict[str, Any] | None = None
    tags: list[str] | None = None
    duration_ms: int | None = Field(None, description="Duration in milliseconds")
    children: list["RunHierarchyNode"] = Field(default_factory=list, description="Child runs")

    @classmethod
    def from_run(cls, run: Any) -> "RunHierarchyNode":
        """Create a RunHierarchyNode from a Run model."""
        duration_ms = None
        if run.start_time and run.end_time:
            delta = run.end_time - run.start_time
            duration_ms = int(delta.total_seconds() * 1000)

        # Keep timestamps in UTC for API responses

        return cls(
            id=run.id,
            name=run.name,
            run_type=run.run_type,
            status=run.status,
            start_time=run.start_time,
            end_time=run.end_time,
            parent_run_id=run.parent_run_id,
            inputs=run.inputs,
            outputs=run.outputs,
            error=run.error,
            extra=run.extra,
            tags=run.tags,
            duration_ms=duration_ms,
            children=[],
        )


class RunHierarchyResponse(BaseModel):
    """Response model for run hierarchy."""

    root_run_id: UUID = Field(description="ID of the root run")
    hierarchy: RunHierarchyNode = Field(description="Hierarchical structure of runs")
    total_runs: int = Field(description="Total number of runs in the hierarchy")
    max_depth: int = Field(description="Maximum depth of the hierarchy")


class DashboardStats(BaseModel):
    """Dashboard statistics response."""

    total_runs: int = Field(description="Total number of runs in the database")
    total_traces: int = Field(description="Total number of root traces")
    recent_runs_24h: int = Field(description="Number of runs in the last 24 hours")
    status_distribution: dict[str, int] = Field(description="Distribution of run statuses")
    run_type_distribution: dict[str, int] = Field(description="Distribution of run types")
    project_distribution: dict[str, int] = Field(description="Distribution by project")


class ProjectInfo(BaseModel):
    """Project information."""

    name: str
    total_runs: int
    total_traces: int
    last_activity: datetime | None = None


class DashboardSummary(BaseModel):
    """Complete dashboard summary response."""

    stats: DashboardStats
    recent_projects: list[ProjectInfo] = Field(description="Recently active projects")
    timestamp: datetime = Field(description="When this summary was generated")


# Update forward references for recursive model
RunHierarchyNode.model_rebuild()
