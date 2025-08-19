"""Protobuf parser for OpenTelemetry OTLP data."""

from typing import Any

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue
from opentelemetry.proto.resource.v1.resource_pb2 import Resource
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span

from src.core.logging import get_logger

logger = get_logger(__name__)


def parse_protobuf_request(body: bytes) -> dict[str, Any]:
    """
    Parse OTLP protobuf request and convert to JSON format.

    Args:
        body: Raw protobuf bytes from HTTP request

    Returns:
        Dict containing the parsed data in JSON-compatible format
    """
    try:
        logger.info(f"🔍 DEBUG: Starting protobuf parsing of {len(body)} bytes")

        # Parse the protobuf message
        export_request = ExportTraceServiceRequest()
        export_request.ParseFromString(body)

        logger.info(f"🔍 DEBUG: Successfully parsed protobuf message with {len(export_request.resource_spans)} resource spans")

        # Convert to JSON-compatible format
        result = {"resourceSpans": []}

        for i, resource_span in enumerate(export_request.resource_spans):
            logger.info(f"🔍 DEBUG: Converting resource span #{i + 1}")
            json_resource_span = convert_resource_spans_to_json(resource_span)
            result["resourceSpans"].append(json_resource_span)

        logger.info(f"✅ DEBUG: Successfully parsed protobuf request with {len(result['resourceSpans'])} resource spans")
        return result

    except Exception as e:
        logger.error(f"❌ DEBUG: Failed to parse protobuf request: {e}")
        raise ValueError(f"Invalid protobuf data: {e}")


def convert_resource_spans_to_json(resource_span: ResourceSpans) -> dict[str, Any]:
    """Convert ResourceSpans protobuf message to JSON format."""
    result = {"resource": convert_resource_to_json(resource_span.resource), "scopeSpans": []}

    for scope_spans in resource_span.scope_spans:
        json_scope_spans = convert_scope_spans_to_json(scope_spans)
        result["scopeSpans"].append(json_scope_spans)

    return result


def convert_resource_to_json(resource: Resource) -> dict[str, Any]:
    """Convert Resource protobuf message to JSON format."""
    return {"attributes": [convert_key_value_to_json(attr) for attr in resource.attributes]}


def convert_scope_spans_to_json(scope_spans: ScopeSpans) -> dict[str, Any]:
    """Convert ScopeSpans protobuf message to JSON format."""
    return {
        "scope": {"name": scope_spans.scope.name, "version": scope_spans.scope.version},
        "spans": [convert_span_to_json(span) for span in scope_spans.spans],
    }


def convert_span_to_json(span: Span) -> dict[str, Any]:
    """Convert Span protobuf message to JSON format."""
    logger.info(f"🔍 DEBUG: Converting span: {span.name} (ID: {span.span_id.hex() if span.span_id else 'None'})")

    # Convert bytes to proper UUID format for Agent Spy compatibility
    def bytes_to_uuid_format(byte_data: bytes) -> str:
        """Convert bytes to UUID format string."""
        if not byte_data:
            return None
        # Convert to hex and format as UUID
        hex_str = byte_data.hex()
        # Ensure it's 32 characters (16 bytes)
        if len(hex_str) != 32:
            # Pad or truncate to 32 characters
            hex_str = hex_str.ljust(32, "0")[:32]
        # Format as UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

    result = {
        "traceId": bytes_to_uuid_format(span.trace_id) if span.trace_id else None,
        "spanId": bytes_to_uuid_format(span.span_id) if span.span_id else None,
        "parentSpanId": bytes_to_uuid_format(span.parent_span_id) if span.parent_span_id else None,
        "name": span.name,
        "kind": span.kind,
        "startTimeUnixNano": str(span.start_time_unix_nano),
        "endTimeUnixNano": str(span.end_time_unix_nano),
        "attributes": [convert_key_value_to_json(attr) for attr in span.attributes],
        "events": [convert_event_to_json(event) for event in span.events],
        "links": [convert_link_to_json(link) for link in span.links],
        "status": convert_status_to_json(span.status),
    }

    logger.info(f"✅ DEBUG: Successfully converted span: {span.name}")
    return result


def convert_key_value_to_json(key_value: KeyValue) -> dict[str, Any]:
    """Convert KeyValue protobuf message to JSON format."""
    return {"key": key_value.key, "value": convert_any_value_to_json(key_value.value)}


def convert_any_value_to_json(any_value: AnyValue) -> dict[str, Any]:
    """Convert AnyValue protobuf message to JSON format."""
    if any_value.HasField("string_value"):
        return {"stringValue": any_value.string_value}
    elif any_value.HasField("bool_value"):
        return {"boolValue": any_value.bool_value}
    elif any_value.HasField("int_value"):
        return {"intValue": any_value.int_value}
    elif any_value.HasField("double_value"):
        return {"doubleValue": any_value.double_value}
    elif any_value.HasField("array_value"):
        return {"arrayValue": {"values": [convert_any_value_to_json(val) for val in any_value.array_value.values]}}
    elif any_value.HasField("kvlist_value"):
        return {"kvlistValue": {"values": [convert_key_value_to_json(kv) for kv in any_value.kvlist_value.values]}}
    elif any_value.HasField("bytes_value"):
        return {"bytesValue": any_value.bytes_value.hex()}
    else:
        return {"stringValue": ""}  # Default fallback


def convert_event_to_json(event) -> dict[str, Any]:
    """Convert Span.Event protobuf message to JSON format."""
    return {
        "timeUnixNano": str(event.time_unix_nano),
        "name": event.name,
        "attributes": [convert_key_value_to_json(attr) for attr in event.attributes],
        "droppedAttributesCount": event.dropped_attributes_count,
    }


def convert_link_to_json(link) -> dict[str, Any]:
    """Convert Span.Link protobuf message to JSON format."""

    # Convert bytes to proper UUID format for Agent Spy compatibility
    def bytes_to_uuid_format(byte_data: bytes) -> str:
        """Convert bytes to UUID format string."""
        if not byte_data:
            return None
        # Convert to hex and format as UUID
        hex_str = byte_data.hex()
        # Ensure it's 32 characters (16 bytes)
        if len(hex_str) != 32:
            # Pad or truncate to 32 characters
            hex_str = hex_str.ljust(32, "0")[:32]
        # Format as UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"

    return {
        "traceId": bytes_to_uuid_format(link.trace_id) if link.trace_id else None,
        "spanId": bytes_to_uuid_format(link.span_id) if link.span_id else None,
        "attributes": [convert_key_value_to_json(attr) for attr in link.attributes],
        "droppedAttributesCount": link.dropped_attributes_count,
    }


def convert_status_to_json(status) -> dict[str, Any]:
    """Convert Status protobuf message to JSON format."""
    return {"code": status.code, "message": status.message}


def validate_protobuf_data(body: bytes) -> bool:
    """
    Validate that the body contains valid OTLP protobuf data.

    Args:
        body: Raw bytes to validate

    Returns:
        True if valid protobuf data, False otherwise
    """
    try:
        export_request = ExportTraceServiceRequest()
        export_request.ParseFromString(body)
        return True
    except Exception:
        return False
