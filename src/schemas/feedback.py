"""Pydantic models for feedback data compatible with LangSmith."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FeedbackBase(BaseModel):
    """Base model for feedback."""

    score: float | None = Field(None, description="Numeric score")
    value: Any | None = Field(None, description="Feedback value (can be any type)")
    comment: str | None = Field(None, description="Text comment")
    correction: dict[str, Any] | None = Field(None, description="Correction data")
    feedback_group_id: UUID | None = Field(None, description="Feedback group ID")


class FeedbackCreate(FeedbackBase):
    """Model for creating feedback."""

    run_id: UUID = Field(..., description="Run ID this feedback is for")
    key: str = Field(..., description="Feedback key/type")

    # Optional fields
    id: UUID | None = Field(default_factory=uuid4, description="Feedback ID")
    created_at: datetime | None = Field(None, description="Creation time")
    modified_at: datetime | None = Field(None, description="Modification time")

    # Source information
    source_info: dict[str, Any] | None = Field(None, description="Source information")
    feedback_source: dict[str, Any] | None = Field(None, description="Feedback source")


class FeedbackUpdate(FeedbackBase):
    """Model for updating feedback."""

    # All fields optional for updates
    key: str | None = None
    modified_at: datetime | None = None


class FeedbackResponse(FeedbackCreate):
    """Model for feedback responses."""

    # Always present in responses
    id: UUID = Field(..., description="Feedback ID")
    created_at: datetime = Field(..., description="Creation time")
    modified_at: datetime = Field(..., description="Last modification time")

    # Additional response fields
    session_id: UUID | None = Field(None, description="Session ID")
    comparative_experiment_id: UUID | None = Field(None, description="Comparative experiment ID")
