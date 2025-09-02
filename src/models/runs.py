"""SQLAlchemy model for runs (traces and spans)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import GUID, Base, ProjectMixin, TimestampMixin, datetime_to_utc_iso


class Run(Base, TimestampMixin, ProjectMixin):
    """
    SQLAlchemy model for runs (traces and spans).

    This model stores both traces (root runs) and spans (child runs).
    The parent_run_id field is None for traces and set for spans.
    """

    __tablename__ = "runs"

    # Primary key
    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, index=True)

    # Basic run information
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Timing information
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Hierarchy - parent_run_id is None for root traces
    parent_run_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True, index=True)

    # Data fields (stored as JSON)
    inputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    serialized: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    events: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    # Error information
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tags (stored as JSON array)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Reference to example (for evaluation)
    reference_example_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True, index=True)

    # Status information
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running", index=True)

    # Add composite indexes for common queries
    __table_args__ = (
        # Index for finding child runs of a parent
        Index("idx_runs_parent_start", "parent_run_id", "start_time"),
        # Index for project queries with time filtering
        Index("idx_runs_project_time", "project_name", "start_time"),
        # Index for run type queries
        Index("idx_runs_type_time", "run_type", "start_time"),
        # Index for status queries
        Index("idx_runs_status_time", "status", "start_time"),
    )

    @property
    def execution_time(self) -> float | None:
        """
        Calculate execution time in seconds.

        Returns:
            Execution time in seconds if both start_time and end_time are available,
            None otherwise.
        """
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds()
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "run_type": self.run_type,
            "start_time": datetime_to_utc_iso(self.start_time),
            "end_time": datetime_to_utc_iso(self.end_time),
            "parent_run_id": str(self.parent_run_id) if self.parent_run_id else None,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "extra": self.extra,
            "serialized": self.serialized,
            "events": self.events,
            "error": self.error,
            "tags": self.tags,
            "reference_example_id": str(self.reference_example_id) if self.reference_example_id else None,
            "status": self.status,
            "project_name": self.project_name,
            "created_at": datetime_to_utc_iso(self.created_at),
            "updated_at": datetime_to_utc_iso(self.updated_at),
        }

    def __repr__(self) -> str:
        """String representation of the run."""
        return f"<Run(id={self.id}, name='{self.name}', type='{self.run_type}', status='{self.status}')>"
