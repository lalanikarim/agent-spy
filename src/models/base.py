"""Base model class for SQLAlchemy models."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, TypeDecorator, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, str):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            from uuid import UUID

            if not isinstance(value, UUID):
                return UUID(value)
            return value


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


def get_uuid_column():
    """Get UUID column type based on database dialect."""
    return mapped_column(GUID(), primary_key=True, default=uuid4, index=True)


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )


class ProjectMixin:
    """Mixin to add project information."""

    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
