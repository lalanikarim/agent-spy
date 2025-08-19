"""Validation utilities for OpenTelemetry integration."""

import uuid
from datetime import datetime
from typing import Any


def validate_otlp_span(span_data: dict[str, Any]) -> bool:
    """Validate OTLP span data structure."""
    required_fields = ["trace_id", "span_id", "name", "kind", "start_time"]

    for field in required_fields:
        if field not in span_data:
            return False

    # Validate trace_id and span_id format
    try:
        uuid.UUID(span_data["trace_id"])
        uuid.UUID(span_data["span_id"])
    except (ValueError, TypeError):
        return False

    # Validate kind is an integer
    if not isinstance(span_data["kind"], int):
        return False

    # Validate start_time is a datetime
    return isinstance(span_data["start_time"], datetime)


def validate_agent_spy_run(run_data: dict[str, Any]) -> bool:
    """Validate Agent Spy run data structure."""
    required_fields = ["id", "name", "run_type", "start_time"]

    for field in required_fields:
        if field not in run_data:
            return False

    # Validate UUID format
    try:
        uuid.UUID(run_data["id"])
    except (ValueError, TypeError):
        return False

    # Validate start_time is a datetime
    return isinstance(run_data["start_time"], datetime)


def validate_otlp_resource(resource_data: dict[str, Any]) -> bool:
    """Validate OTLP resource data structure."""
    # Resource should have attributes
    if "attributes" not in resource_data:
        return False

    return isinstance(resource_data["attributes"], dict)


def validate_otlp_status(status_data: dict[str, Any]) -> bool:
    """Validate OTLP status data structure."""
    # Status should have a code
    if "code" not in status_data:
        return False

    if not isinstance(status_data["code"], int):
        return False

    # Code should be valid
    return status_data["code"] in [0, 1, 2]


def sanitize_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """Sanitize OTLP attributes to ensure they're JSON serializable."""
    sanitized = {}

    for key, value in attributes.items():
        if isinstance(value, str | int | float | bool | type(None)):
            sanitized[key] = value
        elif isinstance(value, list | tuple):
            # Convert lists/tuples to strings if they contain non-serializable items
            try:
                sanitized[key] = list(value)
            except (TypeError, ValueError):
                sanitized[key] = str(value)
        else:
            # Convert other types to strings
            sanitized[key] = str(value)

    return sanitized


def validate_trace_id_format(trace_id: str) -> bool:
    """Validate trace ID format (32 hex characters)."""
    if len(trace_id) != 32:
        return False

    try:
        int(trace_id, 16)
        return True
    except ValueError:
        return False


def validate_span_id_format(span_id: str) -> bool:
    """Validate span ID format (16 hex characters)."""
    if len(span_id) != 16:
        return False

    try:
        int(span_id, 16)
        return True
    except ValueError:
        return False
