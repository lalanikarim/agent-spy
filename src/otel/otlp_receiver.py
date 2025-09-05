"""Simplified OpenTelemetry receiver for Agent Spy."""

from concurrent import futures
from datetime import UTC
from typing import Any

import grpc
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc

from src.api.websocket import manager as websocket_manager
from src.core.database import get_db_session
from src.core.logging import get_logger
from src.repositories.runs import RunRepository
from src.schemas.runs import RunCreate

logger = get_logger(__name__)


class OtlpReceiver:
    """Simplified OTLP receiver handling both HTTP and gRPC protocols."""

    def __init__(self, http_path: str = "/v1/traces", grpc_host: str = "127.0.0.1", grpc_port: int = 4317):
        self.http_path = http_path
        self.grpc_host = grpc_host
        self.grpc_port = grpc_port
        self.router = APIRouter(prefix=http_path, tags=["opentelemetry"])
        self.grpc_server = None
        self._setup_http_routes()

    def _setup_http_routes(self):
        """Setup HTTP routes for OTLP trace export."""

        @self.router.get("/")
        async def health_check():
            """Health check endpoint for OTLP receiver."""
            return JSONResponse(content={"status": "healthy", "service": "otlp-http-receiver"})

        # Support non-trailing-slash variant for health
        @self.router.get("")
        async def health_check_no_slash():
            return JSONResponse(content={"status": "healthy", "service": "otlp-http-receiver"})

        @self.router.post("/")
        async def export_traces(request: Request):
            """Handle OTLP HTTP trace export."""
            try:
                content_type = request.headers.get("content-type", "")
                if "application/x-protobuf" not in content_type:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported content type: {content_type}. Only application/x-protobuf is supported.",
                    )

                body = await request.body()
                # Decompress if gzip encoded (common default for OTLP HTTP exporter)
                content_encoding = request.headers.get("content-encoding", "").lower()
                if content_encoding == "gzip":
                    import gzip

                    try:
                        body = gzip.decompress(body)
                    except Exception as e:
                        raise HTTPException(status_code=400, detail=f"Failed to decompress gzip body: {e}")
                if not body:
                    raise HTTPException(status_code=400, detail="Empty request body")

                # Parse protobuf and convert to runs
                runs_to_create = await self._process_otlp_data(body)

                # Store runs in database
                created_runs = await self.store_runs(runs_to_create)

                # Broadcast WebSocket events
                await self.broadcast_events(created_runs)

                return JSONResponse(content={"status": "success", "spans_processed": len(created_runs)})

            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                logger.error(f"Error processing OTLP HTTP request: {e}")
                # Check if it's a database-related error
                if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                    logger.warning("Duplicate key detected, some spans may already exist")
                    return JSONResponse(
                        content={"status": "partial_success", "spans_processed": 0, "message": "Some spans already exist"}
                    )
                elif "transaction has been rolled back" in str(e):
                    logger.error("Database transaction error, database may be in inconsistent state")
                    return JSONResponse(
                        content={"status": "error", "spans_processed": 0, "message": "Database transaction error"}
                    )
                else:
                    raise HTTPException(status_code=500, detail=str(e))

        # Support non-trailing-slash variant for POST
        @self.router.post("")
        async def export_traces_no_slash(request: Request):
            return await export_traces(request)

    async def _process_otlp_data(self, body: bytes) -> list[RunCreate]:
        """Process OTLP protobuf data and convert to Agent Spy runs."""
        try:
            # Import here to avoid circular imports
            from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

            # Parse protobuf
            request = trace_service_pb2.ExportTraceServiceRequest()
            request.ParseFromString(body)

            runs_to_create = []
            seen_span_ids = set()  # Track seen span IDs to avoid duplicates

            for resource_spans in request.resource_spans:
                # Extract resource attributes
                resource_attrs = {}
                if resource_spans.resource and resource_spans.resource.attributes:
                    for attr in resource_spans.resource.attributes:
                        if attr.value.HasField("string_value"):
                            resource_attrs[attr.key] = attr.value.string_value
                        elif attr.value.HasField("int_value"):
                            resource_attrs[attr.key] = attr.value.int_value
                        elif attr.value.HasField("double_value"):
                            resource_attrs[attr.key] = attr.value.double_value
                        elif attr.value.HasField("bool_value"):
                            resource_attrs[attr.key] = attr.value.bool_value

                # Process spans (support both scope_spans and instrumentation_library_spans)
                scope_spans_list = list(resource_spans.scope_spans)
                if not scope_spans_list and hasattr(resource_spans, "instrumentation_library_spans"):
                    scope_spans_list = list(resource_spans.instrumentation_library_spans)

                for scope_spans in scope_spans_list:
                    for span_proto in scope_spans.spans:
                        # Skip if we've already seen this span ID
                        span_id = span_proto.span_id.hex()
                        if span_id in seen_span_ids:
                            logger.debug(f"Skipping duplicate span ID: {span_id}")
                            continue
                        seen_span_ids.add(span_id)

                        run_create = self.convert_span_to_run(span_proto, resource_attrs)
                        if run_create:
                            runs_to_create.append(run_create)

            return runs_to_create

        except Exception as e:
            logger.error(f"Error processing OTLP data: {e}")
            # Return 400 for protobuf parsing errors
            if "Error parsing message" in str(e):
                raise HTTPException(status_code=400, detail="Invalid protobuf data")
            raise

    def convert_span_to_run(self, span_proto, resource_attrs: dict[str, Any]) -> RunCreate | None:
        """Convert OTLP span to Agent Spy run."""
        try:
            # Extract basic span information (hex strings)
            trace_id_hex = span_proto.trace_id.hex()
            span_id_hex = span_proto.span_id.hex()
            parent_span_id_hex = span_proto.parent_span_id.hex() if span_proto.parent_span_id else None

            # Deterministically derive UUIDs from trace/span ids (OTLP ids are 8/16 bytes, not UUIDs)
            from uuid import NAMESPACE_OID, uuid5

            derived_run_id = uuid5(NAMESPACE_OID, f"{trace_id_hex}:{span_id_hex}")
            derived_parent_id = uuid5(NAMESPACE_OID, f"{trace_id_hex}:{parent_span_id_hex}") if parent_span_id_hex else None

            # Convert timestamps
            start_time = self._nanos_to_datetime(span_proto.start_time_unix_nano)
            end_time = self._nanos_to_datetime(span_proto.end_time_unix_nano) if span_proto.end_time_unix_nano else None

            # Determine status
            status = "running"
            if end_time:
                status = "failed" if span_proto.status.code == 2 else "completed"

            # Collect span attributes into a dict for richer extraction
            attributes: dict[str, Any] = {}
            if span_proto.attributes:
                for attr in span_proto.attributes:
                    attributes[attr.key] = self._extract_attribute_value(attr.value)

            # Determine run_type
            run_type = (
                "llm"
                if any(k.startswith("llm.") for k in attributes) or attributes.get("langsmith.span.kind") == "LLM"
                else "chain"
            )

            # Extract inputs (prompts, workflow inputs)
            inputs: dict[str, Any] = {}
            try:
                # Collect prompts from llm.prompt.*.content
                prompts = [
                    v
                    for k, v in attributes.items()
                    if k.startswith("llm.prompt") and k.endswith(".content") and isinstance(v, str)
                ]
                if prompts:
                    inputs["prompts"] = prompts
                # Generic input and request.* keys
                for key, value in attributes.items():
                    if key.startswith("input.") or key.startswith("request."):
                        inputs[key.split(".", 1)[1]] = value
                # Common workflow input keys
                if "workflow.input.topic" in attributes:
                    inputs["topic"] = attributes["workflow.input.topic"]
            except Exception:
                pass

            # Extract outputs (completions, usage)
            outputs: dict[str, Any] = {}
            try:
                completions = [
                    v
                    for k, v in attributes.items()
                    if k.startswith("llm.completion") and k.endswith(".content") and isinstance(v, str)
                ]
                if completions:
                    outputs["text"] = completions[0]
                    outputs["completions"] = completions
                # Generic output.* keys
                for key, value in attributes.items():
                    if key.startswith("output."):
                        outputs[key.split(".", 1)[1]] = value
                # Usage metrics
                usage: dict[str, Any] = {}
                if "llm.usage.prompt_tokens" in attributes:
                    usage["prompt_tokens"] = attributes["llm.usage.prompt_tokens"]
                if "llm.usage.completion_tokens" in attributes:
                    usage["completion_tokens"] = attributes["llm.usage.completion_tokens"]
                if "llm.usage.total_tokens" in attributes:
                    usage["total_tokens"] = attributes["llm.usage.total_tokens"]
                if usage:
                    outputs["usage"] = usage
            except Exception:
                pass

            # Extract project name from resource
            project_name = resource_attrs.get("service.name", "unknown")

            # Build events from span events if present
            events: list[dict[str, Any]] = []
            try:
                if getattr(span_proto, "events", None):
                    for ev in span_proto.events:
                        ev_attrs: dict[str, Any] = {}
                        for a in ev.attributes:
                            ev_attrs[a.key] = self._extract_attribute_value(a.value)
                        events.append(
                            {
                                "name": ev.name,
                                "time": self._nanos_to_datetime(ev.time_unix_nano),
                                "attributes": ev_attrs or None,
                            }
                        )
            except Exception:
                pass

            # Derive tags from resource and selected attributes
            tag_keys = list(resource_attrs.keys())
            for k in ("llm.vendor", "llm.request.model", "workflow.name", "step.name"):
                if k in attributes:
                    tag_keys.append(f"{k}={attributes[k]}")

            # Create run
            return RunCreate(
                id=derived_run_id,
                name=span_proto.name,
                run_type=run_type,
                start_time=start_time,
                end_time=end_time,
                parent_run_id=derived_parent_id,
                inputs=inputs or {"span_id": span_id_hex},
                outputs=outputs or ({"status": "completed"} if end_time else {}),
                extra={
                    "otlp_span_kind": span_proto.kind,
                    "otlp.trace_id": trace_id_hex,
                    "otlp.span_id": span_id_hex,
                    **({"otlp.parent_span_id": parent_span_id_hex} if parent_span_id_hex else {}),
                    **(
                        {"llm.model": attributes.get("llm.response.model") or attributes.get("llm.request.model")}
                        if (attributes.get("llm.response.model") or attributes.get("llm.request.model"))
                        else {}
                    ),
                },
                serialized=None,
                events=events,
                error=None if status != "failed" else "OTLP span error",
                tags=tag_keys,
                reference_example_id=None,
                project_name=project_name,
            )

        except Exception as e:
            logger.error(f"Error converting span {span_proto.span_id.hex()}: {e}")
            return None

    def _extract_attribute_value(self, value) -> Any:
        """Extract value from OTLP attribute."""
        if value.HasField("string_value"):
            return value.string_value
        elif value.HasField("int_value"):
            return value.int_value
        elif value.HasField("double_value"):
            return value.double_value
        elif value.HasField("bool_value"):
            return value.bool_value
        return str(value)

    def _nanos_to_datetime(self, nanos: int) -> Any:
        """Convert nanoseconds to datetime."""
        from datetime import datetime

        if nanos == 0:
            return None
        return datetime.fromtimestamp(nanos / 1_000_000_000, tz=UTC)

    async def store_runs(self, runs_to_create: list[RunCreate]) -> list[Any]:
        """Store runs in database."""
        if not runs_to_create:
            return []

        created_runs = []
        async with get_db_session() as session:
            try:
                run_repository = RunRepository(session)
                for run_create in runs_to_create:
                    try:
                        # Check if run already exists to avoid duplicate key errors
                        existing_run = await run_repository.get_by_id(run_create.id)
                        if existing_run:
                            logger.debug(f"Run {run_create.id} already exists, skipping creation")
                            created_runs.append(existing_run)
                            continue

                        created_run = await run_repository.create(run_create, disable_events=True)
                        created_runs.append(created_run)
                    except Exception as e:
                        logger.error(f"Error creating run {run_create.id}: {e}")
                        # Continue with next run instead of failing the entire batch
                        continue

                # Commit the transaction if we have any successful creations
                if created_runs:
                    await session.commit()

            except Exception as e:
                logger.error(f"Database session error: {e}")
                await session.rollback()
                # Return empty list on session error to avoid further issues
                return []

        return created_runs

    async def broadcast_events(self, created_runs: list[Any]):
        """Broadcast WebSocket events for created runs."""
        for run in created_runs:
            try:
                await websocket_manager.broadcast_event(
                    "trace.created",
                    {
                        "trace_id": str(run.id),
                        "name": run.name,
                        "run_type": run.run_type,
                        "project_name": run.project_name,
                        "source": "otlp_simple",
                    },
                )

                if run.status == "completed":
                    await websocket_manager.broadcast_event(
                        "trace.completed",
                        {
                            "trace_id": str(run.id),
                            "name": run.name,
                            "run_type": run.run_type,
                            "project_name": run.project_name,
                            "source": "otlp_simple",
                            "execution_time": run.execution_time,
                        },
                    )

            except Exception as e:
                logger.error(f"Error broadcasting event for run {run.id}: {e}")

        # Forward to OTLP endpoints (fire and forget)
        try:
            from src.core.otlp_forwarder import get_otlp_forwarder

            otlp_forwarder = get_otlp_forwarder()
            if otlp_forwarder and otlp_forwarder.tracer:
                await otlp_forwarder.forward_runs(created_runs)
                logger.debug(f"OTLP forwarding initiated for {len(created_runs)} OTLP traces")
        except Exception as e:
            logger.warning(f"Failed to forward OTLP traces to OTLP endpoints: {e}")

    async def start_grpc_server(self):
        """Start gRPC server for OTLP trace export."""
        try:
            # Create gRPC server
            self.grpc_server = grpc.aio.server(
                futures.ThreadPoolExecutor(max_workers=10),
                options=[
                    ("grpc.max_send_message_length", 50 * 1024 * 1024),
                    ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ],
            )

            # Add trace service
            trace_service = OtlpTraceService(self)
            trace_service_pb2_grpc.add_TraceServiceServicer_to_server(trace_service, self.grpc_server)

            # Bind to port
            bind_address = f"{self.grpc_host}:{self.grpc_port}"
            try:
                self.grpc_server.add_insecure_port(bind_address)
            except Exception as bind_err:
                logger.warning(f"Failed to bind OTLP gRPC server to {bind_address}: {bind_err}. Falling back to 0.0.0.0.")
                fallback_address = f"0.0.0.0:{self.grpc_port}"
                self.grpc_server.add_insecure_port(fallback_address)
                bind_address = fallback_address

            # Start server
            await self.grpc_server.start()
            logger.info(f"OTLP gRPC server started on {bind_address}")

        except Exception as e:
            logger.error(f"Failed to start OTLP gRPC server: {e}")
            raise

    async def stop_grpc_server(self):
        """Stop gRPC server."""
        if self.grpc_server:
            try:
                await self.grpc_server.stop(grace=5)
                logger.info("OTLP gRPC server stopped")
            except Exception as e:
                logger.error(f"Error stopping OTLP gRPC server: {e}")


class OtlpTraceService(trace_service_pb2_grpc.TraceServiceServicer):
    """Simplified OTLP trace service for gRPC."""

    def __init__(self, receiver: OtlpReceiver):
        self.receiver = receiver

    async def Export(self, request, context):
        """Handle OTLP gRPC trace export requests."""
        try:
            logger.debug(f"Received OTLP gRPC export request with {len(request.resource_spans)} resource spans")

            # Convert OTLP spans to runs
            runs_to_create = []

            for resource_spans in request.resource_spans:
                # Extract resource attributes (protobuf repeated field)
                resource_attrs = {}
                if resource_spans.resource and resource_spans.resource.attributes:
                    for attr in resource_spans.resource.attributes:
                        if attr.value.HasField("string_value"):
                            resource_attrs[attr.key] = attr.value.string_value
                        elif attr.value.HasField("int_value"):
                            resource_attrs[attr.key] = attr.value.int_value
                        elif attr.value.HasField("double_value"):
                            resource_attrs[attr.key] = attr.value.double_value
                        elif attr.value.HasField("bool_value"):
                            resource_attrs[attr.key] = attr.value.bool_value

                # Process spans (support both scope_spans and instrumentation_library_spans)
                scope_spans_list = list(resource_spans.scope_spans)
                if not scope_spans_list and hasattr(resource_spans, "instrumentation_library_spans"):
                    scope_spans_list = list(resource_spans.instrumentation_library_spans)

                for scope_spans in scope_spans_list:
                    for span_proto in scope_spans.spans:
                        run_create = self.receiver.convert_span_to_run(span_proto, resource_attrs)
                        if run_create:
                            runs_to_create.append(run_create)

            # Store runs and broadcast events
            if runs_to_create:
                created_runs = await self.receiver.store_runs(runs_to_create)
                await self.receiver.broadcast_events(created_runs)
                logger.info(f"Successfully processed {len(runs_to_create)} spans from gRPC")

            return trace_service_pb2.ExportTraceServiceResponse()

        except Exception as e:
            logger.error(f"Error processing OTLP gRPC request: {e}")
            context.abort(grpc.StatusCode.INTERNAL, str(e))
