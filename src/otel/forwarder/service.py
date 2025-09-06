"""OTLP Forwarder Service using OpenTelemetry SDK."""

import asyncio
from contextlib import suppress
from typing import Any, cast

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPSpanExporterGrpc
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.core.logging import get_logger
from src.models.runs import Run

from .config import OtlpForwarderConfig

logger = get_logger(__name__)


class OtlpForwarderService:
    """Service for forwarding Agent Spy traces to OTLP endpoints using OpenTelemetry SDK"""

    def __init__(self, config: OtlpForwarderConfig):
        self.config = config
        self.tracer_provider: TracerProvider | None = None
        self.tracer: trace.Tracer | None = None
        # Pending groups: group_key -> {"runs": {run_id: Run}, "task": asyncio.Task}
        self._pending_groups: dict[str, dict[str, Any]] = {}
        self._debounce_seconds: float = 5.0
        self._setup_tracer()

    def _setup_tracer(self):
        """Setup OpenTelemetry tracer for forwarding"""
        if not self.config.enabled or not self.config.endpoint:
            logger.info("OTLP forwarder disabled or no endpoint configured")
            return

        try:
            # Create resource with service name
            resource = Resource.create({"service.name": self.config.service_name})

            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)

            # Create exporter based on protocol
            if self.config.protocol == "grpc":
                exporter = OTLPSpanExporterGrpc(
                    endpoint=self.config.endpoint,
                    timeout=self.config.timeout,
                    headers=self.config.headers,
                    insecure=True,  # Use insecure connection for development
                )
            else:
                exporter = OTLPSpanExporter(
                    endpoint=self.config.endpoint, timeout=self.config.timeout, headers=self.config.headers
                )

            # Add batch processor
            processor = BatchSpanProcessor(exporter)
            self.tracer_provider.add_span_processor(processor)

            # Set as global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            # Create tracer
            self.tracer = trace.get_tracer("agent-spy-forwarder")

            logger.info(f"OTLP forwarder configured: {self.config.protocol}://{self.config.endpoint}")

        except Exception as e:
            logger.error(f"Failed to setup OTLP forwarder: {e}")
            self.tracer = None

    async def forward_runs(self, runs: list[Run]) -> None:
        """Forward Agent Spy runs to OTLP endpoint, grouped to preserve hierarchy."""
        if not self.tracer or not runs:
            return

        try:
            logger.debug(f"Forwarding {len(runs)} runs to OTLP endpoint (buffered group)")
            # Buffer runs into pending groups by original trace id
            self._buffer_runs(runs)
        except Exception as e:
            logger.error(f"Error initiating OTLP forwarding: {e}")

    async def _forward_runs_async(self, runs: list[Run]) -> None:
        """Asynchronously forward runs to OTLP endpoint"""
        try:
            for run in runs:
                # Add timeout to prevent hanging
                try:
                    await asyncio.wait_for(self._forward_single_run(run), timeout=30.0)
                except TimeoutError:
                    logger.error(f"Timeout forwarding run {run.id} to OTLP")
                except Exception as e:
                    logger.error(f"Error forwarding run {run.id}: {e}")

        except Exception as e:
            logger.error(f"Error in async OTLP forwarding: {e}")

    async def _forward_runs_grouped_async(self, runs: list[Run]) -> None:
        """Group runs by original OTLP trace id (if present) and preserve parent-child hierarchy."""
        try:
            tracer = self.tracer
            if tracer is None:
                logger.warning("Cannot forward grouped runs: tracer not initialized")
                return
            # Build groups by root grouping key:
            # 1) Prefer extra.root_run_id if present (Agent Spy/LangSmith)
            # 2) Else prefer original otlp/trace.id attribute
            # 3) Else fallback to run.id
            groups: dict[str, list[Run]] = {}
            for run in runs:
                group_key = None
                try:
                    extra = getattr(run, "extra", None) or {}
                    group_key = str(extra.get("root_run_id") or extra.get("otlp.trace_id") or extra.get("trace.id") or "")
                except Exception:
                    group_key = ""
                if not group_key:
                    group_key = str(getattr(run, "id", "ungrouped"))
                groups.setdefault(group_key, []).append(run)

            for group_key, group_runs in groups.items():
                # Replace group runs with authoritative DB hierarchy if we can infer a root id
                try:
                    candidate_root = None
                    for r in group_runs:
                        if getattr(r, "parent_run_id", None) is None:
                            candidate_root = getattr(r, "id", None)
                            break
                    if candidate_root is None and group_runs:
                        # Fallback: take any run and walk up parents from DB
                        from src.core.database import get_db_session
                        from src.repositories.runs import RunRepository

                        any_run = group_runs[0]
                        start_parent = getattr(any_run, "parent_run_id", None)
                        if start_parent is not None:
                            async with get_db_session() as session:
                                repo = RunRepository(session)
                                current_id = start_parent
                                visited: set[str] = set()
                                while current_id and str(current_id) not in visited:
                                    visited.add(str(current_id))
                                    parent = await repo.get_by_id(current_id)
                                    if not parent or not getattr(parent, "parent_run_id", None):
                                        candidate_root = getattr(parent, "id", None) if parent else None
                                        break
                                    current_id = getattr(parent, "parent_run_id", None)
                    if candidate_root is not None:
                        from src.core.database import get_db_session
                        from src.repositories.runs import RunRepository

                        async with get_db_session() as session:
                            repo = RunRepository(session)
                            hierarchy_runs = await repo.get_run_hierarchy(candidate_root)
                            if hierarchy_runs:
                                group_runs = hierarchy_runs
                                logger.debug(f"Using DB hierarchy ({len(group_runs)}) for grouped trace {group_key}")
                except Exception as _:
                    pass
                # Index by id and build children mapping
                by_id: dict[str, Run] = {}
                children: dict[str | None, list[Run]] = {}
                for r in group_runs:
                    rid = str(getattr(r, "id", ""))
                    pid = getattr(r, "parent_run_id", None)
                    by_id[rid] = r
                    children.setdefault(str(pid) if pid else None, []).append(r)

                # Identify roots (no parent in this group)
                roots = []
                for r in group_runs:
                    pid = getattr(r, "parent_run_id", None)
                    if not pid or str(pid) not in by_id:
                        roots.append(r)

                # Create a trace per root and add descendants
                for root in roots:
                    try:
                        # Compute timing
                        start_ns, end_ns = self._compute_run_times_ns(root)
                        # Start root span
                        root_span = tracer.start_span(
                            name=getattr(root, "name", "root"),
                            attributes=self._extract_attributes(root),
                            start_time=start_ns if start_ns is not None else None,
                        )
                        # Build spans under root
                        from opentelemetry import trace as ot_trace

                        with ot_trace.use_span(root_span, end_on_exit=False):
                            await self._create_descendant_spans(tracer, root, children, by_id)
                        # End root span with original end time if available
                        if end_ns is not None:
                            root_span.end(end_time=end_ns)
                        else:
                            root_span.end()
                        logger.info(f"✅ Forwarded grouped trace for root {getattr(root, 'id', '?')} with group {group_key}")
                    except Exception as e:
                        logger.error(f"Error forwarding grouped trace for root {getattr(root, 'id', '?')}: {e}")
        except Exception as e:
            logger.error(f"Error in grouped OTLP forwarding: {e}")

    def _buffer_runs(self, runs: list[Run]) -> None:
        """Add runs to pending groups and debounce a grouped send."""
        for run in runs:
            # Prefer explicit root_run_id when available (Agent Spy/LangSmith),
            # then original OTLP trace id attributes
            group_key: str | None = None
            try:
                extra = getattr(run, "extra", None) or {}
                group_key = str(extra.get("root_run_id") or extra.get("otlp.trace_id") or extra.get("trace.id") or "")
            except Exception:
                group_key = ""

            # For LangSmith/AgentSpy runs, derive grouping by root (top-most parent) id when no OTLP trace id
            if not group_key:
                parent_id = getattr(run, "parent_run_id", None)
                if parent_id:
                    # If a parent bucket exists, prefer it
                    pid_str = str(parent_id)
                    if pid_str in self._pending_groups:
                        group_key = pid_str
                    else:
                        # If any existing bucket contains the parent, use that bucket's key
                        for existing_key, bucket in self._pending_groups.items():
                            try:
                                runs_map = cast(dict[str, Run], bucket.get("runs") or {})
                                if pid_str in runs_map:
                                    group_key = existing_key
                                    break
                            except Exception:
                                pass
                        # Fallback: group under immediate parent id
                        if not group_key:
                            group_key = pid_str
                else:
                    # Root without OTLP id groups by its own id
                    group_key = str(getattr(run, "id", "ungrouped"))

            bucket = self._pending_groups.get(group_key)
            if bucket is None:
                bucket = {"runs": {}, "task": None}
                self._pending_groups[group_key] = bucket
            # Deduplicate by run id
            try:
                run_id = str(getattr(run, "id", None) or id(run))
            except Exception:
                run_id = str(id(run))
            runs_dict = cast(dict[str, Run], bucket["runs"])
            runs_dict[run_id] = run

            # If we grouped this run under its own id but its parent bucket appears later, merge buckets
            # (Lightweight best-effort merge when parent bucket already exists now)
            parent_id = getattr(run, "parent_run_id", None)
            if parent_id:
                pid_str = str(parent_id)
                parent_bucket = self._pending_groups.get(pid_str)
                if parent_bucket is not None and group_key != pid_str:
                    # Move current bucket's runs into parent bucket and replace reference
                    try:
                        current_bucket = self._pending_groups.pop(group_key, None)
                        if current_bucket is not None:
                            cur_map = cast(dict[str, Run], current_bucket.get("runs") or {})
                            parent_map = cast(dict[str, Run], parent_bucket.get("runs") or {})
                            parent_map.update(cur_map)
                            # Cancel current task and restart parent's debounce
                            with suppress(Exception):
                                t = current_bucket.get("task")
                                if t and not t.done():
                                    t.cancel()
                            # Restart parent debounce to account for new runs
                            t_parent = parent_bucket.get("task")
                            if t_parent and not t_parent.done():
                                with suppress(Exception):
                                    t_parent.cancel()
                            parent_bucket["task"] = asyncio.create_task(self._debounced_flush(pid_str))
                            # Update group_key reference
                            group_key = pid_str
                    except Exception:
                        pass

            # (Re)start debounce task
            task = bucket.get("task")
            if task and not task.done():
                # Cancel previous task to extend debounce window
                with suppress(Exception):
                    task.cancel()
            new_task = asyncio.create_task(self._debounced_flush(group_key))
            bucket["task"] = new_task

    async def _debounced_flush(self, group_key: str) -> None:
        """Wait debounce window, then flush the grouped runs to the exporter."""
        try:
            await asyncio.sleep(self._debounce_seconds)
            bucket = self._pending_groups.pop(group_key, None)
            if not bucket:
                return
            runs = list(bucket.get("runs", {}).values())
            # Enrich: if group_key or buffered runs can identify a root, load full hierarchy from DB
            try:
                from uuid import UUID

                root_uuid = None
                try:
                    root_uuid = UUID(group_key)
                except Exception:
                    root_uuid = None
                candidate_root = None
                if root_uuid is not None:
                    candidate_root = root_uuid
                else:
                    # Pick any run without parent as candidate root
                    for r in runs:
                        if getattr(r, "parent_run_id", None) is None:
                            candidate_root = getattr(r, "id", None)
                            break
                    # If not found in buffered runs, derive by walking parents via DB from any run
                    if candidate_root is None and runs:
                        from src.core.database import get_db_session
                        from src.repositories.runs import RunRepository

                        any_run = runs[0]
                        start_parent = getattr(any_run, "parent_run_id", None)
                        if start_parent is not None:
                            async with get_db_session() as session:
                                repo = RunRepository(session)
                                # walk up chain to root
                                current_id = start_parent
                                visited: set[str] = set()
                                while current_id and str(current_id) not in visited:
                                    visited.add(str(current_id))
                                    parent = await repo.get_by_id(current_id)
                                    if not parent or not getattr(parent, "parent_run_id", None):
                                        candidate_root = getattr(parent, "id", None) if parent else None
                                        break
                                    current_id = getattr(parent, "parent_run_id", None)
                if candidate_root is not None:
                    from src.core.database import get_db_session
                    from src.repositories.runs import RunRepository

                    async with get_db_session() as session:
                        repo = RunRepository(session)
                        hierarchy = await repo.get_run_hierarchy(candidate_root)
                        # Merge DB runs with buffered runs (prefer buffered objects)
                        by_id: dict[str, Run] = {str(getattr(r, "id", "")): r for r in runs}
                        for r in hierarchy:
                            rid = str(getattr(r, "id", ""))
                            if rid not in by_id:
                                by_id[rid] = r
                        runs = list(by_id.values())
            except Exception as enrich_err:
                logger.debug(f"Could not enrich group {group_key} from DB: {enrich_err}")
            if not runs:
                return
            logger.info(f"🚚 Flushing grouped OTLP trace {group_key} with {len(runs)} runs after debounce")
            await self._forward_runs_grouped_async(runs)
        except asyncio.CancelledError:
            # Debounce restarted; ignore
            pass
        except Exception as e:
            logger.error(f"Error during debounced flush for group {group_key}: {e}")

    async def _create_descendant_spans(
        self, tracer: trace.Tracer, parent: Run, children: dict[str | None, list[Run]], by_id: dict[str, Run]
    ) -> None:
        """Create spans for all descendants of parent using parent-child relationships."""
        try:
            parent_id = str(getattr(parent, "id", ""))
            for child in children.get(parent_id, []) or []:
                try:
                    start_ns, end_ns = self._compute_run_times_ns(child)
                    with tracer.start_as_current_span(
                        name=getattr(child, "name", "child"),
                        start_time=start_ns if start_ns is not None else None,
                        end_on_exit=False,
                        attributes=self._extract_attributes(child),
                    ) as child_span:
                        # Recurse to grandchildren
                        await self._create_descendant_spans(tracer, child, children, by_id)
                        # End child span
                        if end_ns is not None:
                            child_span.end(end_time=end_ns)
                        else:
                            child_span.end()
                except Exception as ce:
                    logger.error(f"Error creating child span for run {getattr(child, 'id', '?')}: {ce}")
        except Exception as e:
            logger.error(f"Error walking descendants for run {getattr(parent, 'id', '?')}: {e}")

    def _compute_run_times_ns(self, run: Run) -> tuple[int | None, int | None]:
        """Compute nanosecond start/end from run fields, tolerant to types."""
        start_time_ns = None
        end_time_ns = None
        try:
            from datetime import datetime

            if getattr(run, "start_time", None):
                st = run.start_time
                try:
                    ts_method = getattr(st, "timestamp", None)
                    if callable(ts_method):
                        start_time_ns = int(float(ts_method()) * 1_000_000_000)
                    else:
                        start_time_ns = int(datetime.fromisoformat(str(st).replace("Z", "+00:00")).timestamp() * 1_000_000_000)
                except Exception as inner:
                    logger.debug(f"Could not parse start_time for run {getattr(run, 'id', '?')}: {inner}")
            if getattr(run, "end_time", None):
                et = run.end_time
                try:
                    te_method = getattr(et, "timestamp", None)
                    if callable(te_method):
                        end_time_ns = int(float(te_method()) * 1_000_000_000)
                    else:
                        end_time_ns = int(datetime.fromisoformat(str(et).replace("Z", "+00:00")).timestamp() * 1_000_000_000)
                except Exception as inner:
                    logger.debug(f"Could not parse end_time for run {getattr(run, 'id', '?')}: {inner}")
        except Exception as e:
            logger.debug(f"Could not compute times for run {getattr(run, 'id', '?')}: {e}")
        return start_time_ns, end_time_ns

    async def _forward_single_run(self, run: Run) -> None:
        """Forward a single run to OTLP endpoint"""
        if not self.tracer:
            logger.warning(f"Cannot forward run {run.id}: tracer not initialized")
            return

        try:
            # Convert Agent Spy timing to nanoseconds for OpenTelemetry
            start_time_ns = None
            end_time_ns = None

            if run.start_time:
                try:
                    from datetime import datetime

                    st = run.start_time
                    ts_method = getattr(st, "timestamp", None)
                    if callable(ts_method):
                        start_time_ns = int(float(ts_method()) * 1_000_000_000)
                    else:
                        start_dt = datetime.fromisoformat(str(st).replace("Z", "+00:00"))
                        start_time_ns = int(start_dt.timestamp() * 1_000_000_000)
                    logger.info(f"🕐 Parsed start_time for run {run.id}: {run.start_time} -> {start_time_ns}")
                except Exception as e:
                    logger.warning(f"Could not parse start_time for run {run.id}: {e}")

            if run.end_time:
                try:
                    from datetime import datetime

                    et = run.end_time
                    te_method = getattr(et, "timestamp", None)
                    if callable(te_method):
                        end_time_ns = int(float(te_method()) * 1_000_000_000)
                    else:
                        end_dt = datetime.fromisoformat(str(et).replace("Z", "+00:00"))
                        end_time_ns = int(end_dt.timestamp() * 1_000_000_000)
                    logger.info(f"🕐 Parsed end_time for run {run.id}: {run.end_time} -> {end_time_ns}")
                except Exception as e:
                    logger.warning(f"Could not parse end_time for run {run.id}: {e}")

            # Create span with original timing using the working pattern
            if start_time_ns is not None and end_time_ns is not None:
                duration_sec = (end_time_ns - start_time_ns) / 1_000_000_000
                logger.info(
                    f"🕐 Creating span with custom timing for run {run.id}: "
                    + f"start={start_time_ns}, end={end_time_ns}, duration={duration_sec:.2f}s"
                )

                # Pattern 1: Create span with start_time, use_span, end with end_time
                span = self.tracer.start_span(
                    name=run.name, attributes=self._extract_attributes(run), start_time=start_time_ns
                )

                # Set the span as current for child spans
                with trace.use_span(span, end_on_exit=False):
                    # Add events if available
                    if run.events:
                        for event in run.events:
                            span.add_event(name=event.get("name", "event"), attributes=event.get("attributes", {}))

                    # Add status
                    if run.status == "failed" and run.error:
                        span.set_status(trace.Status(trace.StatusCode.ERROR, run.error))
                    elif run.status == "completed":
                        span.set_status(trace.Status(trace.StatusCode.OK))

                    # For any trace with step-like information in outputs, create child spans
                    if run.outputs and self._has_step_like_outputs(run.outputs):
                        logger.info(f"🔄 Creating step spans for run {run.id} with {len(run.outputs)} outputs")
                        # Create child spans synchronously within the parent span context
                        self._create_step_spans_sync(span, run)
                    else:
                        has_steps = self._has_step_like_outputs(run.outputs) if run.outputs else False
                        logger.debug(
                            f"ℹ️ No step extraction for run {run.id}: " + f"outputs={bool(run.outputs)}, has_steps={has_steps}"
                        )

                # End the span with original end time
                span.end(end_time=end_time_ns)
                logger.info(
                    f"✅ Ended span for run {run.id} with custom timing - "
                    + f"Trace ID: {span.get_span_context().trace_id}, Start: {start_time_ns}, End: {end_time_ns}"
                )

            else:
                # Fallback to current timing if original timing not available
                with self.tracer.start_as_current_span(
                    name=run.name,
                    attributes=self._extract_attributes(run),
                    end_on_exit=True,  # Auto-end the span
                ) as span:
                    # Add events if available
                    if run.events:
                        for event in run.events:
                            span.add_event(name=event.get("name", "event"), attributes=event.get("attributes", {}))

                    # Add status
                    if run.status == "failed" and run.error:
                        span.set_status(trace.Status(trace.StatusCode.ERROR, run.error))
                    elif run.status == "completed":
                        span.set_status(trace.Status(trace.StatusCode.OK))

                    # For any trace with step-like information in outputs, create child spans
                    if run.outputs and self._has_step_like_outputs(run.outputs):
                        logger.info(f"🔄 Creating step spans for run {run.id} with {len(run.outputs)} outputs")
                        # Create child spans synchronously within the parent span context
                        self._create_step_spans_sync(span, run)
                    else:
                        has_steps = self._has_step_like_outputs(run.outputs) if run.outputs else False
                        logger.debug(
                            f"ℹ️ No step extraction for run {run.id}: " + f"outputs={bool(run.outputs)}, has_steps={has_steps}"
                        )

        except Exception as e:
            logger.error(f"Error forwarding run {run.id} to OTLP: {e}")

    def _has_step_like_outputs(self, outputs: dict) -> bool:
        """Check if outputs contain step-like information that should be broken into child spans"""
        if not outputs:
            return False

        # Look for patterns that indicate step-like outputs
        step_indicators = [
            # Common step patterns
            "step",
            "stage",
            "phase",
            "iteration",
            "round",
            # LangChain/LangGraph specific patterns
            "formatted_prompt",
            "initial_response",
            "extracted_info",
            "refined_analysis",
            "structured_content",
            "final_analysis",
            "validation_result",
            # Generic workflow patterns
            "input",
            "output",
            "result",
            "response",
            "answer",
            # Sequential patterns
            "first",
            "second",
            "third",
            "final",
            "last",
        ]

        # Check if any output keys contain step-like patterns
        for key in outputs:
            key_lower = key.lower()
            if any(indicator in key_lower for indicator in step_indicators):
                return True

        # Also check if we have multiple outputs that look like a workflow
        # But be more conservative - only if we have 3+ outputs AND they look like steps
        if len(outputs) >= 3:
            # Additional check: make sure they're not just simple key-value pairs
            step_like_count = 0
            for key in outputs:
                key_lower = key.lower()
                if any(indicator in key_lower for indicator in step_indicators):
                    step_like_count += 1

            # Only consider it step-like if at least 2 outputs look like steps
            if step_like_count >= 2:
                return True

        return False

    def _create_step_spans_sync(self, parent_span, run: Run) -> None:
        """Create child spans synchronously for any trace with step-like outputs"""
        try:
            outputs = run.outputs
            if not outputs:
                return

            logger.info(f"📋 Creating spans for {len(outputs)} outputs: {list(outputs.keys())}")

            # Limit the number of child spans to prevent performance issues
            max_spans = 10
            span_count = 0

            # Create child spans for each output that looks like a step
            for step_key, step_data in outputs.items():
                if span_count >= max_spans:
                    logger.warning(f"Reached maximum number of child spans ({max_spans}) for run {run.id}")
                    break

                if step_data:  # Only create spans for non-empty outputs
                    # Generate a human-readable step name
                    step_name = self._generate_step_name(step_key, step_data)
                    logger.info(f"🔧 Creating span for step: {step_key} -> {step_name}")

                    # Create child span synchronously within parent context
                    if self.tracer:
                        # Create child span using the parent span's context
                        from opentelemetry import trace

                        with (
                            trace.use_span(parent_span, end_on_exit=False),
                            self.tracer.start_as_current_span(
                                name=f"Step: {step_name}",
                                end_on_exit=True,  # Child spans can auto-end since they inherit parent timing
                            ) as step_span,
                        ):
                            # Add step-specific attributes
                            step_span.set_attribute("step.key", step_key)
                            step_span.set_attribute("step.name", step_name)
                            step_span.set_attribute("step.type", self._get_step_type(step_data))

                            # Add step data as attributes (truncated if too long)
                            self._add_step_data_attributes(step_span, step_data)

                            # Set step status
                            step_span.set_status(trace.Status(trace.StatusCode.OK))

                            span_count += 1
                            logger.info(f"✅ Created span {span_count}: Step: {step_name}")

            logger.info(f"🎯 Created {span_count} child spans for run {run.id}")

        except Exception as e:
            logger.error(f"Error creating step spans: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

    async def _create_step_spans(self, parent_span, run: Run) -> None:
        """Create child spans for any trace with step-like outputs (async version - kept for compatibility)"""
        # Delegate to synchronous version to ensure proper timing
        self._create_step_spans_sync(parent_span, run)

    def _generate_step_name(self, step_key: str, step_data) -> str:
        """Generate a human-readable name for a step based on its key and data"""
        # Try to extract a meaningful name from the step key
        key_parts = step_key.replace("_", " ").split()

        # Common patterns for step naming
        if "formatted" in step_key and "prompt" in step_key:
            return "Prompt Template"
        elif "initial" in step_key and "response" in step_key:
            return "Initial Response"
        elif "extracted" in step_key and "info" in step_key:
            return "Information Extraction"
        elif "refined" in step_key and "analysis" in step_key:
            return "Analysis Refinement"
        elif "structured" in step_key and "content" in step_key:
            return "Content Structuring"
        elif "final" in step_key and "analysis" in step_key:
            return "Final Analysis"
        elif "validation" in step_key and "result" in step_key:
            return "Validation"
        elif "input" in step_key:
            return "Input Processing"
        elif "output" in step_key:
            return "Output Generation"
        elif "result" in step_key:
            return "Result Processing"
        elif "response" in step_key:
            return "Response Generation"
        else:
            # Fallback: capitalize the key parts
            return " ".join(word.capitalize() for word in key_parts)

    def _get_step_type(self, step_data) -> str:
        """Determine the type of step based on its data"""
        if isinstance(step_data, str):
            if len(step_data) > 1000:
                return "long_text"
            else:
                return "text"
        elif isinstance(step_data, dict):
            return "structured_data"
        elif isinstance(step_data, list):
            return "list"
        elif isinstance(step_data, int | float):
            return "numeric"
        else:
            return "unknown"

    def _add_step_data_attributes(self, step_span, step_data) -> None:
        """Add step data as attributes to the span, with appropriate truncation"""
        if isinstance(step_data, str):
            # For strings, add the full content if short, truncated if long
            if len(step_data) <= 500:
                step_span.set_attribute("step.data", step_data)
            else:
                step_span.set_attribute("step.data", step_data[:500] + "...")
                step_span.set_attribute("step.data.length", len(step_data))
        elif isinstance(step_data, dict):
            # For dictionaries, add each key-value pair
            for k, v in step_data.items():
                value_str = str(v)
                if len(value_str) <= 200:
                    step_span.set_attribute(f"step.data.{k}", value_str)
                else:
                    step_span.set_attribute(f"step.data.{k}", value_str[:200] + "...")
                    step_span.set_attribute(f"step.data.{k}.length", len(value_str))
        elif isinstance(step_data, list):
            # For lists, add the first few items
            step_span.set_attribute("step.data.count", len(step_data))
            for i, item in enumerate(step_data[:5]):  # Show first 5 items
                item_str = str(item)
                if len(item_str) <= 200:
                    step_span.set_attribute(f"step.data.item_{i}", item_str)
                else:
                    step_span.set_attribute(f"step.data.item_{i}", item_str[:200] + "...")
        else:
            # For other types, convert to string
            value_str = str(step_data)
            if len(value_str) <= 500:
                step_span.set_attribute("step.data", value_str)
            else:
                step_span.set_attribute("step.data", value_str[:500] + "...")

    def _extract_attributes(self, run: Run) -> dict:
        """Extract attributes from Agent Spy run for OTLP span"""
        from datetime import datetime

        attributes = {
            "run.id": str(run.id),
            "run.type": str(getattr(run, "run_type", "")),
            "run.status": str(getattr(run, "status", "")),
            "project.name": str(getattr(run, "project_name", None) or "unknown"),
        }

        # Parent and trace identifiers if available
        try:
            parent_id = getattr(run, "parent_run_id", None)
            if parent_id:
                attributes["parent_run.id"] = str(parent_id)
        except Exception:
            pass

        try:
            trace_id = getattr(run, "trace_id", None)
            if trace_id:
                attributes["trace.id"] = str(trace_id)
        except Exception:
            pass

        # Add timing information for debugging
        if run.start_time:
            attributes["run.start_time"] = str(run.start_time)
        if run.end_time:
            attributes["run.end_time"] = str(run.end_time)
        if run.start_time and run.end_time:
            # Calculate duration in milliseconds
            try:
                start_dt = datetime.fromisoformat(run.start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(run.end_time.replace("Z", "+00:00"))
                duration_ms = (end_dt - start_dt).total_seconds() * 1000
                attributes["run.duration_ms"] = duration_ms
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not calculate duration for run {run.id}: {e}")

        # Add inputs as attributes
        if run.inputs:
            for key, value in run.inputs.items():
                attributes[f"input.{key}"] = str(value)

        # Add outputs as attributes
        if run.outputs:
            for key, value in run.outputs.items():
                attributes[f"output.{key}"] = str(value)

        # Add tags as attributes
        if run.tags:
            try:
                # Support both dict-like and list-like tags
                if isinstance(run.tags, dict):
                    for key, value in run.tags.items():
                        attributes[f"tag.{key}"] = str(value)
                else:
                    # Treat as a sequence if possible, otherwise stringify
                    try:
                        attributes["run.tags"] = [str(tag) for tag in list(run.tags)]  # type: ignore[arg-type]
                    except Exception:
                        attributes["run.tags"] = str(run.tags)
            except Exception as e:
                logger.debug(f"Could not process tags for run {run.id}: {e}")

        # Add metadata from extra field
        if run.extra:
            for key, value in run.extra.items():
                attributes[f"extra.{key}"] = str(value)

        return attributes

    async def shutdown(self):
        """Shutdown the forwarder service"""
        if self.tracer_provider:
            try:
                # Check if shutdown method is async
                if hasattr(self.tracer_provider, "shutdown"):
                    shutdown_method = self.tracer_provider.shutdown
                    if asyncio.iscoroutinefunction(shutdown_method):
                        await shutdown_method()
                    else:
                        shutdown_method()
                logger.info("OTLP forwarder shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down OTLP forwarder: {e}")
