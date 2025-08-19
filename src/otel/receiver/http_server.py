"""OTLP HTTP server for receiving traces."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.core.database import get_db_session
from src.core.logging import get_logger
from src.otel.receiver.converter import OtlpToAgentSpyConverter
from src.otel.receiver.models import OtlpSpan
from src.otel.receiver.protobuf_parser import parse_protobuf_request, validate_protobuf_data
from src.otel.utils.mapping import (
    bytes_to_hex_string,
    unix_nanos_to_datetime,
)
from src.repositories.runs import RunRepository

logger = get_logger(__name__)


class OtlpHttpServer:
    """OTLP HTTP server for receiving traces."""

    def __init__(self, path: str = "/v1/traces"):
        self.path = path
        self.router = APIRouter(prefix=path, tags=["opentelemetry"])
        self.converter = OtlpToAgentSpyConverter()
        self.run_repository = None
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes."""

        @self.router.post("/")
        async def export_traces(request: Request):
            """Handle OTLP HTTP trace export."""
            try:
                # Get content type
                content_type = request.headers.get("content-type", "")
                logger.info(f"🔍 DEBUG: Received OTLP request with content-type: {content_type}")
                logger.info(f"🔍 DEBUG: Request headers: {dict(request.headers)}")

                # Parse request body - only support standard OTLP protobuf format
                if "application/x-protobuf" in content_type:
                    # Handle protobuf format (standard OpenTelemetry SDK format)
                    body = await request.body()
                    logger.info(f"🔍 DEBUG: Received body size: {len(body)} bytes")

                    if not body:
                        logger.error("❌ DEBUG: Empty request body")
                        raise HTTPException(status_code=400, detail="Empty request body")

                    # Validate protobuf data
                    logger.info("🔍 DEBUG: Validating protobuf data...")
                    if not validate_protobuf_data(body):
                        logger.error("❌ DEBUG: Invalid protobuf data")
                        raise HTTPException(status_code=400, detail="Invalid protobuf data")

                    # Parse protobuf and convert to JSON format for processing
                    logger.info("🔍 DEBUG: Parsing protobuf data...")
                    json_data = parse_protobuf_request(body)
                    logger.info(
                        "✅ DEBUG: Successfully parsed protobuf request with "
                        + f"{len(json_data.get('resourceSpans', []))} resource spans"
                    )

                else:
                    logger.error(f"❌ DEBUG: Unsupported content type: {content_type}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported content type: {content_type}. "
                        + "Only application/x-protobuf is supported for OTLP traces",
                    )

                # Convert and store traces
                runs_to_create = []
                total_spans = 0

                logger.info(f"🔍 DEBUG: Processing {len(json_data.get('resourceSpans', []))} resource spans")

                # Process resource spans
                for i, resource_span_json in enumerate(json_data.get("resourceSpans", [])):
                    logger.info(f"🔍 DEBUG: Processing resource span #{i + 1}")

                    # Extract resource attributes
                    resource_attrs = {}
                    if "resource" in resource_span_json and "attributes" in resource_span_json["resource"]:
                        for attr in resource_span_json["resource"]["attributes"]:
                            if "key" in attr and "value" in attr:
                                key = attr["key"]
                                value = attr["value"]
                                if "stringValue" in value:
                                    resource_attrs[key] = value["stringValue"]
                                elif "intValue" in value:
                                    resource_attrs[key] = value["intValue"]
                                elif "doubleValue" in value:
                                    resource_attrs[key] = value["doubleValue"]
                                elif "boolValue" in value:
                                    resource_attrs[key] = value["boolValue"]

                    logger.info(f"🔍 DEBUG: Extracted resource attributes: {resource_attrs}")

                    # Process scope spans
                    for j, scope_span_json in enumerate(resource_span_json.get("scopeSpans", [])):
                        logger.info(
                            f"🔍 DEBUG: Processing scope span #{j + 1} with {len(scope_span_json.get('spans', []))} spans"
                        )

                        for k, span_json in enumerate(scope_span_json.get("spans", [])):
                            logger.info(f"🔍 DEBUG: Processing span #{k + 1}: {span_json.get('name', 'unknown')}")
                            try:
                                # Convert JSON span to our model
                                span = self._convert_json_span(span_json)
                                logger.info(f"✅ DEBUG: Successfully converted span: {span.name}")

                                # Convert to Agent Spy run
                                run_create = self.converter.convert_span(span, resource_attrs)
                                logger.info(f"✅ DEBUG: Successfully converted to Agent Spy run: {run_create.name}")
                                runs_to_create.append(run_create)
                                total_spans += 1

                            except Exception as e:
                                logger.error(f"❌ DEBUG: Failed to convert span {span_json.get('spanId', 'unknown')}: {e}")
                                # Continue processing other spans
                                continue

                # Create runs
                logger.info(f"🔍 DEBUG: Attempting to create {len(runs_to_create)} runs in database")

                if runs_to_create:
                    try:
                        async with get_db_session() as session:
                            run_repository = RunRepository(session)
                            for i, run_create in enumerate(runs_to_create):
                                logger.info(f"🔍 DEBUG: Creating run #{i + 1}: {run_create.name}")
                                await run_repository.create(run_create, disable_events=True)
                                logger.info(f"✅ DEBUG: Successfully created run: {run_create.name}")
                            # The context manager will handle commit automatically
                        logger.info(
                            f"✅ DEBUG: Successfully created {len(runs_to_create)} runs from {total_spans} spans via HTTP"
                        )
                    except Exception as e:
                        logger.error(f"❌ DEBUG: Failed to create runs via HTTP: {e}")
                        raise HTTPException(status_code=500, detail=f"Failed to store traces: {str(e)}")
                else:
                    logger.warning("⚠️ DEBUG: No runs to create")

                # Return success response
                logger.info(f"✅ DEBUG: Returning success response with {total_spans} spans processed")
                return JSONResponse(
                    status_code=200,
                    content={"status": "success", "spans_processed": total_spans, "content_type": content_type},
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to export traces via HTTP: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/")
        async def health_check():
            """Health check endpoint for OTLP HTTP server."""
            return JSONResponse(
                status_code=200, content={"status": "healthy", "service": "otlp-http-receiver", "endpoint": self.path}
            )

    def _convert_proto_span(self, span_proto) -> OtlpSpan:
        """Convert protobuf span to OtlpSpan model."""
        # Convert trace and span IDs
        trace_id = bytes_to_hex_string(span_proto.trace_id)
        span_id = bytes_to_hex_string(span_proto.span_id)
        parent_span_id = bytes_to_hex_string(span_proto.parent_span_id) if span_proto.parent_span_id else None

        # Convert timestamps
        start_time = unix_nanos_to_datetime(span_proto.start_time_unix_nano)
        end_time = unix_nanos_to_datetime(span_proto.end_time_unix_nano) if span_proto.end_time_unix_nano else None

        # Convert attributes
        attributes = {}
        for attr in span_proto.attributes:
            if attr.key:
                value = self._convert_attribute_value(attr.value)
                if value is not None:
                    attributes[attr.key] = value

        # Convert events
        events = []
        for event_proto in span_proto.events:
            event: dict[str, Any] = {
                "name": event_proto.name,
                "time": unix_nanos_to_datetime(event_proto.time_unix_nano),
                "attributes": {},
            }
            for attr in event_proto.attributes:
                if attr.key:
                    value = self._convert_attribute_value(attr.value)
                    if value is not None:
                        event["attributes"][attr.key] = value
            events.append(event)

        # Convert links
        links = []
        for link_proto in span_proto.links:
            link: dict[str, Any] = {
                "trace_id": bytes_to_hex_string(link_proto.trace_id),
                "span_id": bytes_to_hex_string(link_proto.span_id),
                "attributes": {},
            }
            for attr in link_proto.attributes:
                if attr.key:
                    value = self._convert_attribute_value(attr.value)
                    if value is not None:
                        link["attributes"][attr.key] = value
            links.append(link)

        # Convert status
        status = {"code": span_proto.status.code, "message": span_proto.status.message if span_proto.status.message else None}

        # Create resource dict (will be populated from resource_spans)
        resource = {}

        return OtlpSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=span_proto.name,
            kind=span_proto.kind,
            start_time=start_time,
            end_time=end_time,
            attributes=attributes,
            events=events,
            links=links,
            status=status,
            resource=resource,
        )

    def _convert_json_span(self, span_json: dict) -> OtlpSpan:
        """Convert JSON span to OtlpSpan model."""
        # Convert trace and span IDs
        trace_id = span_json.get("traceId")
        span_id = span_json.get("spanId")
        parent_span_id = span_json.get("parentSpanId")

        # Convert timestamps
        start_time = unix_nanos_to_datetime(int(span_json.get("startTimeUnixNano", 0)))
        end_time = None
        if "endTimeUnixNano" in span_json and span_json["endTimeUnixNano"]:
            end_time = unix_nanos_to_datetime(int(span_json["endTimeUnixNano"]))

        # Convert attributes
        attributes = {}
        for attr in span_json.get("attributes", []):
            if "key" in attr and "value" in attr:
                key = attr["key"]
                value = attr["value"]
                if "stringValue" in value:
                    attributes[key] = value["stringValue"]
                elif "intValue" in value:
                    attributes[key] = value["intValue"]
                elif "doubleValue" in value:
                    attributes[key] = value["doubleValue"]
                elif "boolValue" in value:
                    attributes[key] = value["boolValue"]

        # Convert events
        events = []
        for event_json in span_json.get("events", []):
            event: dict[str, Any] = {
                "name": event_json.get("name", ""),
                "time": unix_nanos_to_datetime(int(event_json.get("timeUnixNano", 0))),
                "attributes": {},
            }
            for attr in event_json.get("attributes", []):
                if "key" in attr and "value" in attr:
                    key = attr["key"]
                    value = attr["value"]
                    if "stringValue" in value:
                        event["attributes"][key] = value["stringValue"]
                    elif "intValue" in value:
                        event["attributes"][key] = value["intValue"]
                    elif "doubleValue" in value:
                        event["attributes"][key] = value["doubleValue"]
                    elif "boolValue" in value:
                        event["attributes"][key] = value["boolValue"]
            events.append(event)

        # Convert links
        links = []
        for link_json in span_json.get("links", []):
            link: dict[str, Any] = {
                "trace_id": link_json.get("traceId"),
                "span_id": link_json.get("spanId"),
                "attributes": {},
            }
            for attr in link_json.get("attributes", []):
                if "key" in attr and "value" in attr:
                    key = attr["key"]
                    value = attr["value"]
                    if "stringValue" in value:
                        link["attributes"][key] = value["stringValue"]
                    elif "intValue" in value:
                        link["attributes"][key] = value["intValue"]
                    elif "doubleValue" in value:
                        link["attributes"][key] = value["doubleValue"]
                    elif "boolValue" in value:
                        link["attributes"][key] = value["boolValue"]
            links.append(link)

        # Convert status
        status_json = span_json.get("status", {})
        status = {"code": status_json.get("code", 0), "message": status_json.get("message")}

        # Create resource dict (will be populated from resource_spans)
        resource = {}

        return OtlpSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=span_json.get("name", ""),
            kind=span_json.get("kind", 0),
            start_time=start_time,
            end_time=end_time,
            attributes=attributes,
            events=events,
            links=links,
            status=status,
            resource=resource,
        )

    def _convert_attribute_value(self, value_proto) -> Any | None:
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
            return self._convert_array_value(value_proto.array_value)
        elif value_proto.HasField("kvlist_value"):
            return self._convert_kvlist_value(value_proto.kvlist_value)
        elif value_proto.HasField("bytes_value"):
            return value_proto.bytes_value
        else:
            return None

    def _convert_array_value(self, array_proto) -> list:
        """Convert protobuf array value to Python list."""
        result = []
        for value in array_proto.values:
            converted = self._convert_attribute_value(value)
            if converted is not None:
                result.append(converted)
        return result

    def _convert_kvlist_value(self, kvlist_proto) -> dict:
        """Convert protobuf kvlist value to Python dict."""
        result = {}
        for kv in kvlist_proto.values:
            if kv.key:
                value = self._convert_attribute_value(kv.value)
                if value is not None:
                    result[kv.key] = value
        return result
