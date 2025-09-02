#!/usr/bin/env python3
# /// script
# dependencies = [
#   "httpx>=0.24.0",
#   "opentelemetry-proto>=1.0.0",
# ]
# ///

"""
Nested Workflow OTLP gRPC Example

This example demonstrates a workflow with:
1. Top-level call that starts tracing
2. Waits for 5 seconds
3. Calls 3 second-level calls
4. Each second-level call has random wait between 5-10 seconds
5. Workflow completion

Traces are sent incrementally:
- When a call starts: trace sent with "running" status (no end_time)
- When a call completes: trace updated with "completed" status (with end_time)

Usage:
    uv run python examples/nested_workflow_otlp_grpc.py
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2
from opentelemetry.proto.trace.v1 import trace_pb2


class NestedWorkflowOTLP:
    def __init__(self, agent_spy_url: str = "http://localhost:8000"):
        self.agent_spy_url = agent_spy_url
        self.service_name = "nested-workflow-service"
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
        status_code: trace_pb2.Status.StatusCode = trace_pb2.Status.StatusCode.STATUS_CODE_UNSET,
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

        # Only set end_time if provided (for completed spans)
        if end_time:
            span.end_time_unix_nano = int(end_time.timestamp() * 1_000_000_000)

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

    async def send_single_span(self, span: trace_pb2.Span):
        """Send a single span to Agent Spy."""
        # Create OTLP request with single span
        request = trace_service_pb2.ExportTraceServiceRequest()

        # Create resource spans
        resource_spans = request.resource_spans.add()

        # Add resource attributes
        resource_attrs = resource_spans.resource.attributes.add()
        resource_attrs.key = "service.name"
        resource_attrs.value.string_value = self.service_name

        resource_attrs = resource_spans.resource.attributes.add()
        resource_attrs.key = "service.version"
        resource_attrs.value.string_value = "1.0.0"

        resource_attrs = resource_spans.resource.attributes.add()
        resource_attrs.key = "deployment.environment"
        resource_attrs.value.string_value = "development"

        # Create scope spans
        scope_spans = resource_spans.scope_spans.add()
        scope_spans.scope.name = "nested-workflow-example"
        scope_spans.scope.version = "1.0.0"

        # Add the single span
        scope_spans.spans.append(span)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.agent_spy_url}/v1/traces/",
                    content=request.SerializeToString(),
                    headers={
                        "Content-Type": "application/x-protobuf",
                        "Accept": "application/json",
                    },
                )

                if response.status_code == 200:
                    return True
                else:
                    print(f"❌ Failed to send span: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Error sending span: {e}")
            return False

    async def simulate_second_level_call(self, call_number: int, parent_span_id: bytes) -> dict[str, Any]:
        """Simulate a second-level call with random wait time."""
        print(f"🔄 Second-level call {call_number} starting...")

        # Random wait time before starting (5-10 seconds)
        pre_start_wait = random.uniform(5.0, 10.0)
        print(f"   ⏳ Waiting {pre_start_wait:.2f}s before starting call {call_number}...")
        await asyncio.sleep(pre_start_wait)

        start_time = datetime.now()
        print(f"   🚀 Call {call_number} actually starting...")

        # Random wait time for the actual work (10-20 seconds)
        work_wait_time = random.uniform(10.0, 20.0)
        print(f"   ⏳ Call {call_number} working for {work_wait_time:.2f}s...")
        await asyncio.sleep(work_wait_time)

        end_time = datetime.now()

        # Create span for this call (COMPLETED - with end_time)
        span_id = self.create_span(
            name=f"second_level_call_{call_number}",
            parent_span_id=parent_span_id,
            attributes={
                "call.number": call_number,
                "call.type": "second_level",
                "operation": "async_processing",
                "component": "workflow_engine",
                "input.data": f"Processing data for call {call_number}",
                "pre_start_wait_seconds": round(pre_start_wait, 2),
                "work_wait_time_seconds": round(work_wait_time, 2),
                "output.result": f"Call {call_number} completed successfully",
                "metadata.call_id": f"call-{call_number}-{int(time.time())}",
            },
            start_time=start_time,
            end_time=end_time,
            status_code=trace_pb2.Status.StatusCode.STATUS_CODE_OK,
        )

        # Send the completed span
        span = next(s for s in self.spans if s.span_id == span_id)
        await self.send_single_span(span)
        print(f"   ✅ Second-level call {call_number} completed in {work_wait_time:.2f}s")
        print(f"   📤 Sent trace for call {call_number} (COMPLETED)")

        return {"call_number": call_number, "duration": work_wait_time, "span_id": span_id, "status": "completed"}

    async def run_nested_workflow(self):
        """Execute the nested workflow."""
        print("🚀 Starting Nested Workflow with OTLP gRPC")
        print("=" * 50)

        workflow_start = datetime.now()

        # Create root span for the entire workflow (will be completed at the end)
        root_span_id = self.create_span(
            name="nested_workflow_root",
            attributes={
                "workflow.name": "nested_workflow_example",
                "workflow.version": "1.0.0",
                "workflow.type": "nested_calls",
                "workflow.trigger": "manual",
                "workflow.user": "test_user",
                "workflow.priority": "normal",
                "input.description": "Nested workflow with 3 second-level calls",
                "component": "workflow_orchestrator",
            },
            start_time=workflow_start,
            # No end_time yet - will be set when workflow completes
        )

        print("📋 Step 1: Top-level call started")
        print("   ⏳ Waiting 5 seconds...")

        # Wait 5 seconds as specified
        await asyncio.sleep(5)

        print("📋 Step 2: Starting 3 second-level calls")

        # Create spans for the 3 second-level calls
        second_level_results = []

        # Run all 3 calls concurrently
        tasks = [self.simulate_second_level_call(i + 1, root_span_id) for i in range(3)]

        # Wait for all calls to complete
        second_level_results = await asyncio.gather(*tasks)

        # Sequential calls after second-level calls
        print("📋 Step 3: Starting sequential calls...")
        sequential_results = []

        for i in range(2):  # Add 2 sequential calls
            call_number = i + 1
            print(f"🔄 Sequential call {call_number} starting...")

            # Random duration between 5-10 seconds
            duration = random.uniform(5.0, 10.0)

            start_time_seq = datetime.now()

            # Simulate the work
            await asyncio.sleep(duration)
            end_time_seq = datetime.now()

            # Create span for sequential call (COMPLETED - with end_time)
            span_id = self.create_span(
                name=f"sequential_call_{call_number}",
                parent_span_id=root_span_id,
                attributes={
                    "call.number": call_number,
                    "call.type": "sequential",
                    "operation": "post_processing",
                    "component": "workflow_engine",
                    "input.data": f"Sequential processing for call {call_number}",
                    "duration_seconds": round(duration, 2),
                    "output.result": f"Sequential call {call_number} completed successfully",
                },
                start_time=start_time_seq,
                end_time=end_time_seq,
                status_code=trace_pb2.Status.StatusCode.STATUS_CODE_OK,
                status_message="Sequential call completed successfully",
            )

            # Send the completed span
            span = next(s for s in self.spans if s.span_id == span_id)
            await self.send_single_span(span)
            print(f"   ✅ Sequential call {call_number} completed in {duration:.2f}s")
            print(f"   📤 Sent trace for sequential call {call_number} (COMPLETED)")

            sequential_results.append(
                {"call_number": call_number, "duration": duration, "span_id": span_id, "status": "completed"}
            )

        # Calculate total duration
        workflow_end = datetime.now()
        total_duration = (workflow_end - workflow_start).total_seconds()

        # Update root span with final attributes and timing (COMPLETING)
        for span in self.spans:
            if span.span_id == root_span_id:
                span.end_time_unix_nano = int(workflow_end.timestamp() * 1_000_000_000)
                span.status.code = trace_pb2.Status.StatusCode.STATUS_CODE_OK

                # Add workflow summary attributes
                summary_attr = span.attributes.add()
                summary_attr.key = "workflow.duration_seconds"
                summary_attr.value.double_value = total_duration

                summary_attr = span.attributes.add()
                summary_attr.key = "workflow.second_level_calls"
                summary_attr.value.int_value = 3

                summary_attr = span.attributes.add()
                summary_attr.key = "workflow.status"
                summary_attr.value.string_value = "completed"

                summary_attr = span.attributes.add()
                summary_attr.key = "output.summary"
                summary_attr.value.string_value = f"Workflow completed: {len(second_level_results)} calls processed"

                # Add individual call results
                for i, result in enumerate(second_level_results):
                    summary_attr = span.attributes.add()
                    summary_attr.key = f"call_{i + 1}_duration"
                    summary_attr.value.double_value = result["duration"]

                # Send updated root span (completed status)
                await self.send_single_span(span)
                break

        print(f"\n🎉 Workflow completed in {total_duration:.2f}s")
        print(f"   Total spans created: {len(self.spans)}")
        print(f"   Second-level calls completed: {len(second_level_results)}")
        print(f"   Sequential calls completed: {len(sequential_results)}")
        print("📤 Sent trace for root workflow (COMPLETED)")

        for result in second_level_results:
            print(f"   - Second-level Call {result['call_number']}: {result['duration']:.2f}s")
        for result in sequential_results:
            print(f"   - Sequential Call {result['call_number']}: {result['duration']:.2f}s")

        print("\n🔍 View your trace in Agent Spy:")
        print(f"   Dashboard: {self.agent_spy_url}")
        print(f"   Trace ID: {self.trace_id.hex()}")
        print("   You should see traces appear in real-time as they start and complete!")

        return True


async def main():
    """Main function to run the nested workflow example."""
    print("🔧 Nested Workflow OTLP gRPC Example (Incremental Traces)")
    print("=" * 55)

    # Create workflow instance
    workflow = NestedWorkflowOTLP()

    # Run the workflow
    success = await workflow.run_nested_workflow()

    if success:
        print("\n✅ Example completed successfully!")
        print("   Check the Agent Spy dashboard to see the trace hierarchy.")
        print("   You should have seen traces appear in real-time!")
    else:
        print("\n❌ Example failed!")
        print("   Make sure Agent Spy is running and accessible.")


if __name__ == "__main__":
    asyncio.run(main())
