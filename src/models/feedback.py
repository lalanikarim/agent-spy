"""SQLAlchemy model for feedback."""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import GUID, Base, TimestampMixin


class Feedback(Base, TimestampMixin):
    """SQLAlchemy model for feedback on runs."""

    __tablename__ = "feedback"

    # Primary key
    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4, index=True)

    # Associated run
    run_id: Mapped[UUID] = mapped_column(GUID(), nullable=False, index=True)

    # Feedback data
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    value: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Source information
    source_info: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    feedback_source_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "score": self.score,
            "value": self.value,
            "comment": self.comment,
            "correction": self.correction,
            "source_info": self.source_info,
            "feedback_source_type": self.feedback_source_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation of the feedback."""
        return f"<Feedback(id={self.id}, run_id={self.run_id}, score={self.score})>"
