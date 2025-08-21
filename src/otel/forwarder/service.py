"""OTLP Forwarder Service using OpenTelemetry SDK."""

import asyncio

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
        self.tracer_provider = None
        self.tracer = None
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
        """Forward Agent Spy runs to OTLP endpoint"""
        if not self.tracer or not runs:
            return

        try:
            logger.debug(f"Forwarding {len(runs)} runs to OTLP endpoint")

            # Process runs asynchronously to avoid blocking
            asyncio.create_task(self._forward_runs_async(runs))

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

                    start_dt = datetime.fromisoformat(run.start_time.replace("Z", "+00:00"))
                    start_time_ns = int(start_dt.timestamp() * 1_000_000_000)  # Convert to nanoseconds
                    logger.info(f"🕐 Parsed start_time for run {run.id}: {run.start_time} -> {start_time_ns}")
                except Exception as e:
                    logger.warning(f"Could not parse start_time for run {run.id}: {e}")

            if run.end_time:
                try:
                    from datetime import datetime

                    end_dt = datetime.fromisoformat(run.end_time.replace("Z", "+00:00"))
                    end_time_ns = int(end_dt.timestamp() * 1_000_000_000)  # Convert to nanoseconds
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
                            f"ℹ️ No step extraction for run {run.id}: "
                            + f"outputs={bool(run.outputs)}, has_steps={has_steps}"
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
                            f"ℹ️ No step extraction for run {run.id}: "
                            + f"outputs={bool(run.outputs)}, has_steps={has_steps}"
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

                        with trace.use_span(parent_span, end_on_exit=False), self.tracer.start_as_current_span(
                            name=f"Step: {step_name}",
                            end_on_exit=True,  # Child spans can auto-end since they inherit parent timing
                        ) as step_span:
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
            "run.id": run.id,
            "run.type": run.run_type,
            "run.status": run.status,
            "project.name": run.project_name or "unknown",
        }

        # Add timing information for debugging
        if run.start_time:
            attributes["run.start_time"] = run.start_time
        if run.end_time:
            attributes["run.end_time"] = run.end_time
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
            for key, value in run.tags.items():
                attributes[f"tag.{key}"] = str(value)

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
