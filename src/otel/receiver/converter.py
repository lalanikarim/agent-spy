"""Convert OpenTelemetry spans to Agent Spy runs."""

from typing import Any
from uuid import UUID

from src.core.logging import get_logger
from src.otel.receiver.models import OtlpSpan
from src.otel.utils.mapping import (
    bytes_to_uuid,
    extract_inputs_from_attributes,
    extract_outputs_from_attributes,
    extract_project_name_from_resource,
    extract_tags_from_attributes,
    map_span_kind_to_run_type,
    map_status_code_to_run_status,
    unix_nanos_to_datetime,
)
from src.otel.utils.validation import sanitize_attributes
from src.schemas.runs import RunCreate

logger = get_logger(__name__)


class OtlpToAgentSpyConverter:
    """Convert OpenTelemetry spans to Agent Spy runs."""

    def convert_span(self, span: OtlpSpan, resource: dict[str, Any]) -> RunCreate:
        """Convert OTLP span to Agent Spy run."""
        try:
            # Use the original span_id as the run ID to preserve parent-child relationships
            # Convert span_id to UUID format for Agent Spy compatibility
            run_uuid = UUID(span.span_id)
            parent_uuid = UUID(span.parent_span_id) if span.parent_span_id else None

            # Map span kind to run type
            run_type = map_span_kind_to_run_type(span.kind)

            # Map status
            status_code = span.status.get("code", 0)
            print(f"DEBUG: Converter received status code: {status_code}")
            status = map_status_code_to_run_status(status_code)
            print(f"DEBUG: Mapped to status: {status}")

            # Extract inputs and outputs from attributes
            inputs = extract_inputs_from_attributes(span.attributes) or {}
            outputs = extract_outputs_from_attributes(span.attributes)

            # Extract project name from resource
            project_name = extract_project_name_from_resource(resource)

            # Extract tags from attributes
            tags = extract_tags_from_attributes(span.attributes)

            # Create extra metadata
            extra = self._create_extra_metadata(span, resource)

            # Create events from span events
            events = self._convert_events(span.events)

            # Determine error message if status is error
            error = None
            if status == "failed":
                error = span.status.get("message", "Unknown error")

            return RunCreate(
                id=run_uuid,
                name=span.name,
                run_type=run_type,
                start_time=span.start_time,
                end_time=span.end_time,
                parent_run_id=parent_uuid,
                inputs=inputs,
                outputs=outputs,
                extra=extra,
                serialized=None,  # OTLP doesn't have serialized data
                events=events,
                error=error,
                tags=tags,
                reference_example_id=None,  # OTLP doesn't have reference examples
                project_name=project_name,
            )

        except Exception as e:
            logger.error(f"Failed to convert OTLP span {span.span_id}: {e}")
            raise

    def _create_extra_metadata(self, span: OtlpSpan, resource: dict[str, Any]) -> dict[str, Any]:
        """Create extra metadata from span and resource data."""
        metadata = {
            "otlp": {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "kind": span.kind,
                "attributes": sanitize_attributes(span.attributes),
                "links": span.links,
            },
            "resource": sanitize_attributes(resource),
        }

        # Add any additional metadata from attributes
        for key, value in span.attributes.items():
            if key.startswith("metadata."):
                metadata_key = key.replace("metadata.", "")
                metadata[metadata_key] = value

        return metadata

    def _convert_events(self, span_events: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        """Convert OTLP span events to Agent Spy events."""
        if not span_events:
            return None

        events = []
        for event in span_events:
            agent_spy_event = {
                "name": event.get("name", "unknown"),
                "timestamp": event.get("time_unix_nano"),
                "attributes": sanitize_attributes(event.get("attributes", {})),
            }
            events.append(agent_spy_event)

        return events

    def convert_protobuf_span(self, protobuf_span, resource_attributes: dict[str, Any]) -> RunCreate:
        """Convert protobuf span to Agent Spy run."""
        # Extract span data from protobuf
        span_data = {
            "trace_id": bytes_to_uuid(protobuf_span.trace_id),
            "span_id": bytes_to_uuid(protobuf_span.span_id),
            "parent_span_id": bytes_to_uuid(protobuf_span.parent_span_id) if protobuf_span.parent_span_id else None,
            "name": protobuf_span.name,
            "kind": protobuf_span.kind,
            "start_time": unix_nanos_to_datetime(protobuf_span.start_time_unix_nano),
            "end_time": unix_nanos_to_datetime(protobuf_span.end_time_unix_nano) if protobuf_span.end_time_unix_nano else None,
            "attributes": self._convert_protobuf_attributes(protobuf_span.attributes),
            "events": self._convert_protobuf_events(protobuf_span.events),
            "links": self._convert_protobuf_links(protobuf_span.links),
            "status": {
                "code": protobuf_span.status.code,
                "message": protobuf_span.status.message,
            },
            "resource": resource_attributes,
        }

        # Create OtlpSpan object
        span = OtlpSpan(**span_data)

        # Convert to Agent Spy run
        return self.convert_span(span, resource_attributes)

    def _convert_protobuf_attributes(self, protobuf_attributes) -> dict[str, Any]:
        """Convert protobuf attributes to dictionary."""
        attributes = {}
        for attr in protobuf_attributes:
            key = attr.key
            value = self._convert_protobuf_value(attr.value)
            attributes[key] = value
        return attributes

    def _convert_protobuf_value(self, protobuf_value) -> Any:
        """Convert protobuf value to Python value."""
        if protobuf_value.HasField("string_value"):
            return protobuf_value.string_value
        elif protobuf_value.HasField("int_value"):
            return protobuf_value.int_value
        elif protobuf_value.HasField("double_value"):
            return protobuf_value.double_value
        elif protobuf_value.HasField("bool_value"):
            return protobuf_value.bool_value
        elif protobuf_value.HasField("array_value"):
            return [self._convert_protobuf_value(v) for v in protobuf_value.array_value.values]
        else:
            return None

    def _convert_protobuf_events(self, protobuf_events) -> list[dict[str, Any]]:
        """Convert protobuf events to list of dictionaries."""
        events = []
        for event in protobuf_events:
            event_data = {
                "name": event.name,
                "time_unix_nano": event.time_unix_nano,
                "attributes": self._convert_protobuf_attributes(event.attributes),
            }
            events.append(event_data)
        return events

    def _convert_protobuf_links(self, protobuf_links) -> list[dict[str, Any]]:
        """Convert protobuf links to list of dictionaries."""
        links = []
        for link in protobuf_links:
            link_data = {
                "trace_id": bytes_to_uuid(link.trace_id),
                "span_id": bytes_to_uuid(link.span_id),
                "attributes": self._convert_protobuf_attributes(link.attributes),
            }
            links.append(link_data)
        return links
