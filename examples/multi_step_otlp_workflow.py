#!/usr/bin/env python3
# /// script
# dependencies = [
#   "httpx>=0.24.0",
#   "opentelemetry-proto>=1.0.0",
# ]
# ///

"""
Multi-Step Workflow OpenTelemetry Example

This example demonstrates how to trace a complex multi-step workflow using OpenTelemetry
and send the traces to Agent Spy via OTLP.

The workflow simulates:
1. Data ingestion
2. Data processing with multiple sub-steps
3. Model inference
4. Result validation
5. Data storage

Each step creates spans with parent-child relationships, showing the complete trace hierarchy.

Usage:
    uv run python examples/multi_step_otlp_workflow.py
"""

import asyncio
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2
from opentelemetry.proto.trace.v1 import trace_pb2


class OTLPWorkflowTracer:
    def __init__(self, agent_spy_url: str = "http://localhost:8000"):
        self.agent_spy_url = agent_spy_url
        self.service_name = "multi-step-workflow"
        self.trace_id = uuid4().bytes  # Single trace ID for entire workflow
        self.spans = []

    def create_span(
        self,
        name: str,
        parent_span_id: bytes = None,
        span_kind: trace_pb2.Span.SpanKind = trace_pb2.Span.SpanKind.SPAN_KIND_INTERNAL,
        attributes: dict[str, Any] = None,
        start_time: datetime = None,
        end_time: datetime = None,
        status_code: trace_pb2.Status.StatusCode = trace_pb2.Status.StatusCode.STATUS_CODE_OK,
        status_message: str = "",
    ) -> bytes:
        """Create a span with the given parameters."""
        span_id = uuid4().bytes
        span = trace_pb2.Span()

        span.name = name
        span.trace_id = self.trace_id
        span.span_id = span_id
        if parent_span_id:
            span.parent_span_id = parent_span_id
        span.kind = span_kind

        # Set timing
        if start_time:
            span.start_time_unix_nano = int(start_time.timestamp() * 1_000_000_000)
        else:
            span.start_time_unix_nano = int(time.time() * 1_000_000_000)

        if end_time:
            span.end_time_unix_nano = int(end_time.timestamp() * 1_000_000_000)
        else:
            span.end_time_unix_nano = span.start_time_unix_nano + int(0.1 * 1_000_000_000)  # 100ms default

        # Set status
        span.status.code = status_code
        if status_message:
            span.status.message = status_message

        # Add attributes
        if attributes:
            for key, value in attributes.items():
                attr = span.attributes.add()
                attr.key = key

                if isinstance(value, str):
                    attr.value.string_value = value
                elif isinstance(value, int):
                    attr.value.int_value = value
                elif isinstance(value, float):
                    attr.value.double_value = value
                elif isinstance(value, bool):
                    attr.value.bool_value = value
                else:
                    attr.value.string_value = str(value)

        self.spans.append(span)
        return span_id

    def simulate_data_ingestion(self) -> bytes:
        """Simulate data ingestion step."""
        print("🔄 Step 1: Data Ingestion")

        start_time = datetime.now()
        time.sleep(0.2)  # Simulate work
        end_time = datetime.now()

        span_id = self.create_span(
            name="data_ingestion",
            attributes={
                "step": "1",
                "operation": "ingest_data",
                "data.source": "user_input",
                "data.format": "json",
                "data.size_mb": 2.5,
                "input.prompt": "Process this customer feedback data",
                "component": "data_pipeline",
            },
            start_time=start_time,
            end_time=end_time,
        )
        print("   ✅ Data ingested successfully")
        return span_id

    def simulate_data_processing(self, parent_span_id: bytes) -> bytes:
        """Simulate data processing with sub-steps."""
        print("🔄 Step 2: Data Processing")

        start_time = datetime.now()

        # Main processing span
        processing_span_id = self.create_span(
            name="data_processing",
            parent_span_id=parent_span_id,
            attributes={
                "step": "2",
                "operation": "process_data",
                "processing.type": "batch",
                "processing.records": 1500,
                "component": "data_pipeline",
            },
            start_time=start_time,
        )

        # Sub-step 1: Data cleaning
        time.sleep(0.1)
        cleaning_start = datetime.now()
        time.sleep(0.15)
        cleaning_end = datetime.now()

        self.create_span(
            name="data_cleaning",
            parent_span_id=processing_span_id,
            attributes={
                "step": "2a",
                "operation": "clean_data",
                "cleaning.method": "regex_validation",
                "cleaning.rules_applied": 5,
                "records.before": 1500,
                "records.after": 1485,
                "records.removed": 15,
                "component": "data_pipeline",
            },
            start_time=cleaning_start,
            end_time=cleaning_end,
        )

        # Sub-step 2: Data transformation
        transform_start = datetime.now()
        time.sleep(0.12)
        transform_end = datetime.now()

        self.create_span(
            name="data_transformation",
            parent_span_id=processing_span_id,
            attributes={
                "step": "2b",
                "operation": "transform_data",
                "transformation.type": "normalization",
                "features.extracted": 12,
                "encoding.method": "one_hot",
                "component": "data_pipeline",
            },
            start_time=transform_start,
            end_time=transform_end,
        )

        # Update processing span end time
        end_time = datetime.now()
        # Find and update the processing span
        for span in self.spans:
            if span.span_id == processing_span_id:
                span.end_time_unix_nano = int(end_time.timestamp() * 1_000_000_000)
                break

        print("   ✅ Data processed successfully (1485 records)")
        return processing_span_id

    def simulate_model_inference(self, parent_span_id: bytes) -> bytes:
        """Simulate model inference step."""
        print("🔄 Step 3: Model Inference")

        start_time = datetime.now()
        time.sleep(0.25)  # Simulate model inference time
        end_time = datetime.now()

        span_id = self.create_span(
            name="model_inference",
            parent_span_id=parent_span_id,
            attributes={
                "step": "3",
                "operation": "model_predict",
                "model.name": "sentiment_classifier_v2",
                "model.version": "2.1.0",
                "model.type": "transformer",
                "model.provider": "huggingface",
                "inference.batch_size": 32,
                "inference.predictions": 1485,
                "inference.confidence_avg": 0.87,
                "tokens.input": 25000,
                "tokens.output": 5000,
                "output.response": "Sentiment analysis completed: 65% positive, 20% neutral, 15% negative",
                "component": "ml_pipeline",
            },
            start_time=start_time,
            end_time=end_time,
        )

        print("   ✅ Model inference completed (avg confidence: 87%)")
        return span_id

    def simulate_result_validation(self, parent_span_id: bytes) -> bytes:
        """Simulate result validation step."""
        print("🔄 Step 4: Result Validation")

        start_time = datetime.now()
        time.sleep(0.08)
        end_time = datetime.now()

        span_id = self.create_span(
            name="result_validation",
            parent_span_id=parent_span_id,
            attributes={
                "step": "4",
                "operation": "validate_results",
                "validation.method": "confidence_threshold",
                "validation.threshold": 0.7,
                "validation.passed": 1420,
                "validation.failed": 65,
                "validation.success_rate": 95.6,
                "quality.score": 0.956,
                "component": "validation_pipeline",
            },
            start_time=start_time,
            end_time=end_time,
        )

        print("   ✅ Results validated (95.6% passed)")
        return span_id

    def simulate_data_storage(self, parent_span_id: bytes) -> bytes:
        """Simulate data storage step."""
        print("🔄 Step 5: Data Storage")

        start_time = datetime.now()
        time.sleep(0.1)
        end_time = datetime.now()

        span_id = self.create_span(
            name="data_storage",
            parent_span_id=parent_span_id,
            attributes={
                "step": "5",
                "operation": "store_results",
                "storage.type": "database",
                "storage.provider": "postgresql",
                "storage.table": "sentiment_results",
                "storage.records_inserted": 1420,
                "storage.batch_size": 100,
                "storage.duration_ms": 100,
                "database.connection_pool": "primary",
                "component": "storage_pipeline",
            },
            start_time=start_time,
            end_time=end_time,
        )

        print("   ✅ Results stored (1420 records)")
        return span_id

    async def send_traces_to_agent_spy(self):
        """Send all collected spans to Agent Spy via OTLP."""
        print(f"\n📤 Sending {len(self.spans)} spans to Agent Spy...")

        # Create OTLP request
        request = trace_service_pb2.ExportTraceServiceRequest()
        resource_spans = request.resource_spans.add()

        # Add resource attributes
        resource = resource_spans.resource

        # Service name
        attr = resource.attributes.add()
        attr.key = "service.name"
        attr.value.string_value = self.service_name

        # Service version
        attr = resource.attributes.add()
        attr.key = "service.version"
        attr.value.string_value = "1.0.0"

        # Deployment environment
        attr = resource.attributes.add()
        attr.key = "deployment.environment"
        attr.value.string_value = "development"

        # Add scope spans
        scope_spans = resource_spans.scope_spans.add()

        # Add all spans to the request
        for span in self.spans:
            scope_spans.spans.append(span)

        # Send to Agent Spy
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_spy_url}/v1/traces/",
                    content=request.SerializeToString(),
                    headers={"Content-Type": "application/x-protobuf"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    print("✅ Successfully sent traces to Agent Spy!")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Spans processed: {result.get('spans_processed')}")
                    return True
                else:
                    print(f"❌ Failed to send traces: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Error sending traces: {e}")
            return False

    async def run_workflow(self):
        """Execute the complete multi-step workflow."""
        print("🚀 Starting Multi-Step Workflow Trace")
        print("=" * 50)

        workflow_start = datetime.now()

        # Create root span for the entire workflow
        root_span_id = self.create_span(
            name="customer_feedback_analysis_workflow",
            attributes={
                "workflow.name": "customer_feedback_analysis",
                "workflow.version": "1.2.0",
                "workflow.trigger": "api_request",
                "workflow.user": "data_analyst",
                "workflow.priority": "normal",
                "input.prompt": "Analyze customer feedback for product sentiment",
                "component": "workflow_orchestrator",
            },
            start_time=workflow_start,
        )

        # Execute workflow steps
        ingestion_span = self.simulate_data_ingestion()
        processing_span = self.simulate_data_processing(ingestion_span)
        inference_span = self.simulate_model_inference(processing_span)
        validation_span = self.simulate_result_validation(inference_span)
        self.simulate_data_storage(validation_span)

        # Complete workflow
        workflow_end = datetime.now()

        # Update root span with final attributes and timing
        for span in self.spans:
            if span.span_id == root_span_id:
                span.end_time_unix_nano = int(workflow_end.timestamp() * 1_000_000_000)

                # Add workflow summary attributes
                duration_ms = int((workflow_end - workflow_start).total_seconds() * 1000)

                summary_attr = span.attributes.add()
                summary_attr.key = "workflow.duration_ms"
                summary_attr.value.int_value = duration_ms

                summary_attr = span.attributes.add()
                summary_attr.key = "workflow.steps_completed"
                summary_attr.value.int_value = 5

                summary_attr = span.attributes.add()
                summary_attr.key = "workflow.status"
                summary_attr.value.string_value = "completed"

                summary_attr = span.attributes.add()
                summary_attr.key = "output.response"
                summary_attr.value.string_value = "Workflow completed successfully: 1420 sentiment predictions stored"

                break

        # Calculate final duration
        duration_ms = int((workflow_end - workflow_start).total_seconds() * 1000)
        print(f"\n🎉 Workflow completed in {duration_ms}ms")
        print(f"   Total spans created: {len(self.spans)}")

        # Send traces to Agent Spy
        success = await self.send_traces_to_agent_spy()

        if success:
            print("\n🔍 View your trace in Agent Spy:")
            print(f"   Dashboard: {self.agent_spy_url}")
            print(f"   Trace ID: {self.trace_id.hex()}")

        return success


async def main():
    """Main function to run the workflow example."""
    print("Multi-Step Workflow OpenTelemetry Tracing Example")
    print("=" * 60)
    print()

    # Check if Agent Spy is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ Agent Spy is not running or not healthy")
                print("   Please start Agent Spy server first:")
                print("   uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to Agent Spy: {e}")
        print("   Please start Agent Spy server first:")
        print("   uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000")
        return False

    print("✅ Agent Spy is running and healthy")
    print()

    # Run the workflow
    tracer = OTLPWorkflowTracer()
    success = await tracer.run_workflow()

    if success:
        print("\n" + "=" * 60)
        print("🎯 Multi-step workflow traced successfully!")
        print("   Check Agent Spy dashboard to see the complete trace hierarchy")
        print("   with parent-child relationships between all workflow steps.")
    else:
        print("\n❌ Failed to trace workflow")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
