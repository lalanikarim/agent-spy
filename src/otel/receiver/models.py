"""OpenTelemetry data models for receiver."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class OtlpSpan:
    """OpenTelemetry span representation."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    kind: int  # SpanKind enum
    start_time: datetime
    end_time: datetime | None
    attributes: dict[str, Any]
    events: list[dict[str, Any]]
    links: list[dict[str, Any]]
    status: dict[str, Any]
    resource: dict[str, Any]


@dataclass
class OtlpResource:
    """OpenTelemetry resource representation."""

    attributes: dict[str, Any]
    dropped_attributes_count: int = 0


@dataclass
class OtlpScope:
    """OpenTelemetry scope representation."""

    name: str
    version: str | None = None
    attributes: dict[str, Any] | None = None
    dropped_attributes_count: int = 0


@dataclass
class OtlpEvent:
    """OpenTelemetry event representation."""

    name: str
    time_unix_nano: int
    attributes: dict[str, Any]
    dropped_attributes_count: int = 0


@dataclass
class OtlpLink:
    """OpenTelemetry link representation."""

    trace_id: str
    span_id: str
    attributes: dict[str, Any]
    dropped_attributes_count: int = 0


@dataclass
class OtlpStatus:
    """OpenTelemetry status representation."""

    code: int  # StatusCode enum
    message: str | None = None


# OpenTelemetry constants
class SpanKind:
    """OpenTelemetry SpanKind constants."""

    SPAN_KIND_UNSPECIFIED = 0
    SPAN_KIND_INTERNAL = 1
    SPAN_KIND_SERVER = 2
    SPAN_KIND_CLIENT = 3
    SPAN_KIND_PRODUCER = 4
    SPAN_KIND_CONSUMER = 5


class StatusCode:
    """OpenTelemetry StatusCode constants."""

    STATUS_CODE_UNSET = 0
    STATUS_CODE_OK = 1
    STATUS_CODE_ERROR = 2
