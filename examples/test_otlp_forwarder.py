#!/usr/bin/env python3
# /// script
# dependencies = [
#   "httpx>=0.24.0",
#   "opentelemetry-proto>=1.0.0",
# ]
# ///

"""
Test OTLP Forwarder Functionality

This script tests the OTLP forwarder by:
1. Creating test traces
2. Enabling the forwarder to send them to another endpoint
3. Verifying the forwarding works

Usage:
    OTLP_FORWARDER_ENABLED=true \\
    OTLP_FORWARDER_ENDPOINT=http://localhost:8000/v1/traces \\
    OTLP_FORWARDER_PROTOCOL=http \\
    uv run python examples/test_otlp_forwarder.py
"""

import os
import sys
import time
from datetime import datetime
from uuid import uuid4

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.otel.forwarder.config import OtlpForwarderConfig
from src.otel.forwarder.service import OtlpForwarderService


def create_test_run():
    """Create a test run object for forwarding."""
    from uuid import UUID

    run_id = str(uuid4())
    trace_id = str(uuid4())
    start_time = datetime.now()

    # Simulate some work
    time.sleep(1)

    end_time = datetime.now()

    # Create a mock run object with all the fields the forwarder expects
    class MockRun:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return MockRun(
        id=UUID(run_id),
        name="test-forwarder-run",
        run_type="chain",
        start_time=start_time.isoformat() + "Z",
        end_time=end_time.isoformat() + "Z",
        status="completed",
        inputs={"test": "input data"},
        outputs={"result": "test output"},
        parent_run_id=None,
        trace_id=UUID(trace_id),
        project_name="test-forwarder",
        extra={"forwarder_test": True},
        events=None,
        error=None,
        tags=None
    )


async def test_forwarder():
    """Test the OTLP forwarder functionality."""
    print("🚀 Testing OTLP Forwarder Functionality")
    print("=" * 50)

    # Check environment variables
    print("🔧 Environment Configuration:")
    print(f"   OTLP_FORWARDER_ENABLED: {os.getenv('OTLP_FORWARDER_ENABLED', 'False')}")
    print(f"   OTLP_FORWARDER_ENDPOINT: {os.getenv('OTLP_FORWARDER_ENDPOINT', 'Not set')}")
    print(f"   OTLP_FORWARDER_PROTOCOL: {os.getenv('OTLP_FORWARDER_PROTOCOL', 'Not set')}")

    # Create forwarder configuration
    config = OtlpForwarderConfig(
        enabled=True,
        endpoint="http://localhost:8000/v1/traces",
        protocol="http",
        service_name="test-forwarder-service",
        timeout=30,
        retry_count=3,
    )

    print("\n📋 Forwarder Configuration:")
    print(f"   Enabled: {config.enabled}")
    print(f"   Endpoint: {config.endpoint}")
    print(f"   Protocol: {config.protocol}")
    print(f"   Service Name: {config.service_name}")

    # Create forwarder service
    print("\n🔧 Creating OTLP Forwarder Service...")
    forwarder = OtlpForwarderService(config)

    if not forwarder.tracer:
        print("❌ Forwarder tracer not initialized!")
        return False

    print("✅ Forwarder service created successfully")

    # Create test runs
    print("\n📝 Creating test runs...")
    test_runs = [create_test_run() for _ in range(3)]

    for i, run in enumerate(test_runs, 1):
        print(f"   Run {i}: {run.id} - {run.name} ({run.status})")

    # Forward the runs
    print(f"\n📤 Forwarding {len(test_runs)} runs...")
    await forwarder.forward_runs(test_runs)

    # Wait a bit for async forwarding to complete
    print("   ⏳ Waiting for forwarding to complete...")
    await asyncio.sleep(2)

    print("✅ Forwarder test completed!")
    print("\n🔍 Check the Agent Spy dashboard to see the forwarded traces:")
    print("   Dashboard: http://localhost:8000")
    print(f"   Look for traces from service: '{config.service_name}'")

    return True


async def main():
    """Main function to run the forwarder test."""
    print("🔧 OTLP Forwarder Test")
    print("=" * 25)

    try:
        success = await test_forwarder()
        if success:
            print("\n✅ Forwarder test completed successfully!")
        else:
            print("\n❌ Forwarder test failed!")
    except Exception as e:
        print(f"\n❌ Error during forwarder test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
