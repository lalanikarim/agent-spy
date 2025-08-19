#!/usr/bin/env python3
# /// script
# dependencies = [
#   "grpcio>=1.59.0",
#   "opentelemetry-proto>=1.0.0",
# ]
# ///

"""
Nested Workflow OTLP gRPC Example (Real gRPC Client)

This example demonstrates a workflow with:
1. Top-level call that starts tracing
2. Waits for 5 seconds
3. Calls 3 second-level calls
4. Each second-level call has random wait between 5-10 seconds
5. Workflow completion

Traces are sent incrementally:
- When a call starts: trace sent with "running" status (no end_time)
- When a call completes: trace updated with "completed" status (with end_time)

This version uses the actual gRPC client to send traces to Agent Spy.

Usage:
    uv run python examples/nested_workflow_otlp_grpc_real.py
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

import grpc
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc
from opentelemetry.proto.trace.v1 import trace_pb2


class NestedWorkflowOTLPgRPC:
    def __init__(self, agent_spy_grpc_url: str = "localhost:4317"):
        self.agent_spy_grpc_url = agent_spy_grpc_url
        self.service_name = "nested-workflow-service-grpc"
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
        """Send a single span to Agent Spy via gRPC."""
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
        scope_spans.scope.name = "nested-workflow-example-grpc"
        scope_spans.scope.version = "1.0.0"

        # Add the single span
        scope_spans.spans.append(span)

        try:
            # Create gRPC channel
            channel = grpc.aio.insecure_channel(self.agent_spy_grpc_url)

            # Create gRPC stub
            stub = trace_service_pb2_grpc.TraceServiceStub(channel)

            # Send traces via gRPC
            await stub.Export(request)

            # Close the channel
            await channel.close()

            return True

        except grpc.RpcError as e:
            print(f"❌ gRPC error sending span: {e.code()}: {e.details()}")
            return False
        except Exception as e:
            print(f"❌ Error sending span: {e}")
            return False

    async def simulate_second_level_call(self, call_number: int, parent_span_id: bytes) -> dict[str, Any]:
        """Simulate a second-level call with random wait time."""
        print(f"🔄 Second-level call {call_number} starting...")

        # Random wait time between 5-10 seconds
        wait_time = random.uniform(5.0, 10.0)

        start_time = datetime.now()

        # Create span for this call (STARTING - no end_time)
        span_id = self.create_span(
            name=f"second_level_call_{call_number}",
            parent_span_id=parent_span_id,
            attributes={
                "call.number": call_number,
                "call.type": "second_level",
                "operation": "async_processing",
                "component": "workflow_engine",
                "input.data": f"Processing data for call {call_number}",
            },
            start_time=start_time,
            # No end_time = running status
        )

        # Send the span immediately when it starts (running status)
        span = next(s for s in self.spans if s.span_id == span_id)
        await self.send_single_span(span)
        print(f"   📤 Sent trace for call {call_number} (RUNNING)")

        # Simulate the work
        await asyncio.sleep(wait_time)
        end_time = datetime.now()

        # Update the span with completion data
        for span in self.spans:
            if span.span_id == span_id:
                span.end_time_unix_nano = int(end_time.timestamp() * 1_000_000_000)
                span.status.code = trace_pb2.Status.StatusCode.STATUS_CODE_OK

                # Add completion attributes
                completion_attr = span.attributes.add()
                completion_attr.key = "wait_time_seconds"
                completion_attr.value.double_value = round(wait_time, 2)

                completion_attr = span.attributes.add()
                completion_attr.key = "output.result"
                completion_attr.value.string_value = f"Call {call_number} completed successfully"

                completion_attr = span.attributes.add()
                completion_attr.key = "metadata.call_id"
                completion_attr.value.string_value = f"call-{call_number}-{int(time.time())}"

                # Send updated span (completed status)
                await self.send_single_span(span)
                break

        print(f"   ✅ Second-level call {call_number} completed in {wait_time:.2f}s")
        print(f"   📤 Sent trace for call {call_number} (COMPLETED)")

        return {"call_number": call_number, "duration": wait_time, "span_id": span_id, "status": "completed"}

    async def run_nested_workflow(self):
        """Execute the nested workflow."""
        print("🚀 Starting Nested Workflow with OTLP gRPC (Real gRPC Client)")
        print("=" * 60)

        workflow_start = datetime.now()

        # Create root span for the entire workflow (STARTING)
        root_span_id = self.create_span(
            name="nested_workflow_root",
            attributes={
                "workflow.name": "nested_workflow_example_grpc",
                "workflow.version": "1.0.0",
                "workflow.type": "nested_calls",
                "workflow.trigger": "manual",
                "workflow.user": "test_user",
                "workflow.priority": "normal",
                "input.description": "Nested workflow with 3 second-level calls (gRPC)",
                "component": "workflow_orchestrator",
            },
            start_time=workflow_start,
            # No end_time = running status
        )

        # Send root span immediately when it starts (running status)
        root_span = next(s for s in self.spans if s.span_id == root_span_id)
        await self.send_single_span(root_span)
        print("📤 Sent trace for root workflow (RUNNING)")

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
        print("📤 Sent trace for root workflow (COMPLETED)")

        for result in second_level_results:
            print(f"   - Call {result['call_number']}: {result['duration']:.2f}s")

        print("\n🔍 View your trace in Agent Spy:")
        print("   Dashboard: http://localhost:8000")
        print(f"   Trace ID: {self.trace_id.hex()}")
        print("   You should see traces appear in real-time as they start and complete!")

        return True


async def main():
    """Main function to run the nested workflow example."""
    print("🔧 Nested Workflow OTLP gRPC Example (Real gRPC Client - Incremental Traces)")
    print("=" * 70)

    # Create workflow instance
    workflow = NestedWorkflowOTLPgRPC()

    # Run the workflow
    success = await workflow.run_nested_workflow()

    if success:
        print("\n✅ Example completed successfully!")
        print("   Check the Agent Spy dashboard to see the trace hierarchy.")
        print("   You should have seen traces appear in real-time!")
    else:
        print("\n❌ Example failed!")
        print("   Make sure Agent Spy is running and accessible on gRPC port 4317.")


if __name__ == "__main__":
    asyncio.run(main())
