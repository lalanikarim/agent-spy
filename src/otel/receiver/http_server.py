"""OTLP HTTP server for receiving traces."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

from src.core.database import get_db_session
from src.core.logging import get_logger
from src.otel.receiver.converter import OtlpToAgentSpyConverter
from src.otel.receiver.models import OtlpSpan
from src.otel.utils.mapping import (
    bytes_to_hex_string,
    extract_resource_attributes,
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

                # Parse request body
                if "application/x-protobuf" in content_type:
                    # Parse protobuf message
                    body = await request.body()
                    export_request = trace_service_pb2.ExportTraceServiceRequest()
                    export_request.ParseFromString(body)
                elif "application/json" in content_type:
                    # Parse JSON message (if supported)
                    body = await request.json()
                    # TODO: Implement JSON parsing for OTLP
                    raise HTTPException(status_code=400, detail="JSON format not yet supported for OTLP HTTP")
                else:
                    raise HTTPException(status_code=400, detail="Unsupported content type. Use application/x-protobuf")

                # Convert and store traces
                runs_to_create = []
                total_spans = 0

                for resource_spans in export_request.resource_spans:
                    # Extract resource attributes
                    resource_attrs = extract_resource_attributes(resource_spans.resource)

                    for scope_spans in resource_spans.scope_spans:
                        for span_proto in scope_spans.spans:
                            try:
                                # Convert protobuf span to our model
                                span = self._convert_proto_span(span_proto)

                                # Convert to Agent Spy run
                                run_create = self.converter.convert_span(span, resource_attrs)
                                runs_to_create.append(run_create)
                                total_spans += 1

                            except Exception as e:
                                logger.error(f"Failed to convert span {span_proto.span_id}: {e}")
                                # Continue processing other spans
                                continue

                # Create runs
                if runs_to_create:
                    try:
                        async with get_db_session() as session:
                            run_repository = RunRepository(session)
                            for run_create in runs_to_create:
                                await run_repository.create(run_create)
                            await session.commit()
                        logger.info(f"Successfully created {len(runs_to_create)} runs from {total_spans} spans via HTTP")
                    except Exception as e:
                        logger.error(f"Failed to create runs via HTTP: {e}")
                        raise HTTPException(status_code=500, detail=f"Failed to store traces: {str(e)}")

                # Return success response
                return JSONResponse(status_code=200, content={"status": "success", "spans_processed": total_spans})

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
