"""Mapping utilities for OpenTelemetry integration."""

from datetime import datetime
from typing import Any


def map_span_kind_to_run_type(kind: int) -> str:
    """Map OTLP SpanKind to Agent Spy run_type."""
    mapping = {
        0: "internal",      # SPAN_KIND_UNSPECIFIED
        1: "internal",      # SPAN_KIND_INTERNAL
        2: "server",        # SPAN_KIND_SERVER
        3: "client",        # SPAN_KIND_CLIENT
        4: "producer",      # SPAN_KIND_PRODUCER
        5: "consumer",      # SPAN_KIND_CONSUMER
    }
    return mapping.get(kind, "custom")


def map_run_type_to_span_kind(run_type: str) -> int:
    """Map Agent Spy run_type to OTLP SpanKind."""
    mapping = {
        "chain": 1,         # INTERNAL
        "llm": 3,           # CLIENT
        "tool": 3,          # CLIENT
        "retrieval": 3,     # CLIENT
        "prompt": 1,        # INTERNAL
        "parser": 1,        # INTERNAL
        "embedding": 3,     # CLIENT
        "server": 2,        # SERVER
        "client": 3,        # CLIENT
        "internal": 1,      # INTERNAL
        "producer": 4,      # PRODUCER
        "consumer": 5,      # CONSUMER
        "custom": 0,        # UNSPECIFIED
    }
    return mapping.get(run_type, 0)


def map_status_code_to_run_status(status_code: int) -> str:
    """Map OTLP StatusCode to Agent Spy status."""
    if status_code == 1:  # STATUS_CODE_OK
        return "completed"
    elif status_code == 2:  # STATUS_CODE_ERROR
        return "failed"
    else:  # STATUS_CODE_UNSET
        return "running"


def map_run_status_to_status_code(status: str) -> int:
    """Map Agent Spy status to OTLP StatusCode."""
    if status == "completed":
        return 1  # STATUS_CODE_OK
    elif status == "failed":
        return 2  # STATUS_CODE_ERROR
    else:
        return 0  # STATUS_CODE_UNSET


def extract_inputs_from_attributes(attributes: dict[str, Any]) -> dict[str, Any] | None:
    """Extract inputs from OTLP span attributes."""
    inputs = {}

    # Look for common input patterns
    for key, value in attributes.items():
        if key.startswith("input.") or key.startswith("request.") or key in ["prompt", "query", "message", "text"]:
            inputs[key] = value

    return inputs if inputs else None


def extract_outputs_from_attributes(attributes: dict[str, Any]) -> dict[str, Any] | None:
    """Extract outputs from OTLP span attributes."""
    outputs = {}

    # Look for common output patterns
    for key, value in attributes.items():
        if key.startswith("output.") or key.startswith("response.") or key in ["result", "response", "answer", "completion"]:
            outputs[key] = value

    return outputs if outputs else None


def extract_project_name_from_resource(resource: dict[str, Any]) -> str | None:
    """Extract project name from OTLP resource attributes."""
    # Common resource attribute keys for project/service name
    project_keys = [
        "service.name",
        "service.namespace",
        "project.name",
        "project.id",
        "deployment.environment",
        "cloud.provider",
    ]

    for key in project_keys:
        if key in resource:
            return str(resource[key])

    return None


def extract_tags_from_attributes(attributes: dict[str, Any]) -> list[str] | None:
    """Extract tags from OTLP span attributes."""
    tags = []

    # Convert relevant attributes to tags
    for key, value in attributes.items():
        if isinstance(value, str | int | float | bool):
            tags.append(f"{key}={value}")

    return tags if tags else None


def datetime_to_unix_nanos(dt: datetime) -> int:
    """Convert datetime to Unix nanoseconds."""
    return int(dt.timestamp() * 1_000_000_000)


def unix_nanos_to_datetime(nanos: int) -> datetime:
    """Convert Unix nanoseconds to datetime."""
    return datetime.fromtimestamp(nanos / 1_000_000_000)


def uuid_to_bytes(uuid_str: str) -> bytes:
    """Convert UUID string to bytes for OTLP."""
    import uuid
    return uuid.UUID(uuid_str).bytes


def bytes_to_uuid(uuid_bytes: bytes) -> str:
    """Convert bytes to UUID string."""
    import uuid
    return str(uuid.UUID(bytes=uuid_bytes))


def bytes_to_hex_string(byte_data: bytes) -> str:
    """Convert bytes to hex string."""
    return byte_data.hex()


def extract_resource_attributes(resource_proto) -> dict[str, Any]:
    """Extract attributes from OTLP resource protobuf."""
    attributes = {}

    if hasattr(resource_proto, 'attributes'):
        for attr in resource_proto.attributes:
            if attr.key:
                value = _convert_proto_attribute_value(attr.value)
                if value is not None:
                    attributes[attr.key] = value

    return attributes


def _convert_proto_attribute_value(value_proto) -> Any | None:
    """Convert protobuf attribute value to Python value."""
    if value_proto.HasField("string_value"):
        return value_proto.string_value
    elif value_proto.HasField("bool_value"):
        return value_proto.bool_value
    elif value_proto.HasField("int_value"):
        return value_proto.int_value
    elif value_proto.HasField("double_value"):
        return value_proto.double_value
    elif value_proto.HasField("array_value"):
        return _convert_proto_array_value(value_proto.array_value)
    elif value_proto.HasField("kvlist_value"):
        return _convert_proto_kvlist_value(value_proto.kvlist_value)
    elif value_proto.HasField("bytes_value"):
        return value_proto.bytes_value
    else:
        return None


def _convert_proto_array_value(array_proto) -> list:
    """Convert protobuf array value to Python list."""
    result = []
    for value in array_proto.values:
        converted = _convert_proto_attribute_value(value)
        if converted is not None:
            result.append(converted)
    return result


def _convert_proto_kvlist_value(kvlist_proto) -> dict:
    """Convert protobuf kvlist value to Python dict."""
    result = {}
    for kv in kvlist_proto.values:
        if kv.key:
            value = _convert_proto_attribute_value(kv.value)
            if value is not None:
                result[kv.key] = value
    return result
