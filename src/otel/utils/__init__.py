"""OpenTelemetry utility functions."""

from .mapping import map_run_type_to_span_kind, map_span_kind_to_run_type
from .validation import validate_agent_spy_run, validate_otlp_span

__all__ = [
    "map_span_kind_to_run_type",
    "map_run_type_to_span_kind",
    "validate_otlp_span",
    "validate_agent_spy_run"
]
