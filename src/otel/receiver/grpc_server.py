"""OTLP gRPC server for Agent Spy."""

import asyncio
from concurrent import futures
from typing import Any

import grpc
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc

from src.api.websocket import manager as websocket_manager
from src.core.database import get_db_session
from src.core.logging import get_logger
from src.otel.receiver.converter import OtlpToAgentSpyConverter
from src.otel.receiver.models import OtlpSpan
from src.otel.utils.mapping import (
    bytes_to_uuid,
    extract_resource_attributes,
    unix_nanos_to_datetime,
)
from src.repositories.runs import RunRepository

logger = get_logger(__name__)


class OtlpTraceService(trace_service_pb2_grpc.TraceServiceServicer):
    """OTLP trace service implementation."""

    def __init__(self, converter: OtlpToAgentSpyConverter, run_repository):
        self.converter = converter
        self.run_repository = run_repository

    async def Export(self, request, context):
        """Handle OTLP trace export requests."""
        try:
            logger.debug(f"Received OTLP export request with {len(request.resource_spans)} resource spans")

            # Convert OTLP spans to Agent Spy runs
            runs_to_create = []
            total_spans = 0

            for resource_spans in request.resource_spans:
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

            # Batch create runs
            created_runs = []
            if runs_to_create:
                try:
                    async with get_db_session() as session:
                        run_repository = RunRepository(session)
                        for run_create in runs_to_create:
                            created_run = await run_repository.create(run_create, disable_events=True)
                            created_runs.append(created_run)
                        # The context manager will handle commit automatically
                    logger.info(f"Successfully created {len(runs_to_create)} runs from {total_spans} spans")

                    # Broadcast WebSocket events for created runs
                    for created_run in created_runs:
                        try:
                            # Always broadcast trace.created
                            await websocket_manager.broadcast_event(
                                "trace.created",
                                {
                                    "trace_id": str(created_run.id),
                                    "name": created_run.name,
                                    "run_type": created_run.run_type,
                                    "project_name": created_run.project_name,
                                    "source": "otlp_grpc",
                                },
                            )
                            logger.info(f"📡 Broadcasted trace.created event for run: {created_run.name}")

                            # If the run is completed, also broadcast trace.completed
                            if created_run.status == "completed":
                                await websocket_manager.broadcast_event(
                                    "trace.completed",
                                    {
                                        "trace_id": str(created_run.id),
                                        "name": created_run.name,
                                        "run_type": created_run.run_type,
                                        "project_name": created_run.project_name,
                                        "source": "otlp_grpc",
                                        "execution_time": created_run.execution_time,
                                    },
                                )
                                logger.info(f"📡 Broadcasted trace.completed event for run: {created_run.name}")

                        except Exception as ws_error:
                            logger.warning(f"⚠️ Failed to broadcast WebSocket event for run {created_run.name}: {ws_error}")
                            # Don't fail the gRPC request if WebSocket fails

                except Exception as e:
                    logger.error(f"Failed to create runs: {e}")
                    context.set_code(grpc.StatusCode.INTERNAL)
                    context.set_details(f"Failed to store traces: {str(e)}")
                    return trace_service_pb2.ExportTraceServiceResponse()

            return trace_service_pb2.ExportTraceServiceResponse()

        except Exception as e:
            logger.error(f"Failed to export traces: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return trace_service_pb2.ExportTraceServiceResponse()

    def _convert_proto_span(self, span_proto) -> OtlpSpan:
        """Convert protobuf span to OtlpSpan model."""
        # Convert trace and span IDs
        trace_id = bytes_to_uuid(span_proto.trace_id)
        span_id = bytes_to_uuid(span_proto.span_id)
        parent_span_id = bytes_to_uuid(span_proto.parent_span_id) if span_proto.parent_span_id else None

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
                "trace_id": bytes_to_uuid(link_proto.trace_id),
                "span_id": bytes_to_uuid(link_proto.span_id),
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


class OtlpGrpcServer:
    """OTLP gRPC server for receiving traces."""

    def __init__(self, host: str = "0.0.0.0", port: int = 4317):  # nosec B104
        self.host = host
        self.port = port
        self.server = None
        self.converter = OtlpToAgentSpyConverter()
        self.run_repository = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Start the gRPC server."""
        try:
            # Create gRPC server
            self.server = grpc.aio.server(
                futures.ThreadPoolExecutor(max_workers=10),
                options=[
                    ("grpc.max_send_message_length", 50 * 1024 * 1024),  # 50MB
                    ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
                ],
            )

            # Register the trace service
            trace_service_pb2_grpc.add_TraceServiceServicer_to_server(
                OtlpTraceService(self.converter, None),  # Repository will be created per request
                self.server,
            )

            # Add insecure port
            listen_addr = f"{self.host}:{self.port}"
            self.server.add_insecure_port(listen_addr)

            # Start server
            await self.server.start()

            logger.info(f"OTLP gRPC server started on {listen_addr}")

            # Wait for shutdown
            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Failed to start OTLP gRPC server: {e}")
            raise

    async def stop(self):
        """Stop the gRPC server."""
        if self.server:
            logger.info("Stopping OTLP gRPC server...")
            await self.server.stop(grace=5)  # 5 second grace period
            logger.info("OTLP gRPC server stopped")

        self._shutdown_event.set()

    def shutdown(self):
        """Trigger shutdown."""
        self._shutdown_event.set()
