"""Integration tests for OpenTelemetry integration."""

from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2
from opentelemetry.proto.trace.v1 import trace_pb2

from src.core.database import close_database, init_database
from src.main import app
from src.repositories.runs import RunRepository


@pytest_asyncio.fixture
async def test_app():
    """Create test application with database."""
    await init_database()
    yield app
    await close_database()


class TestOtlpIntegration:
    """Test OTLP integration end-to-end."""

    def test_otlp_http_health_check(self, test_app):
        """Test OTLP HTTP health check endpoint."""
        from fastapi.testclient import TestClient

        client = TestClient(test_app)

        response = client.get("/v1/traces/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "otlp-http-receiver"

    @pytest.mark.asyncio
    async def test_otlp_http_trace_export(self, test_app):
        """Test OTLP HTTP trace export."""
        from fastapi.testclient import TestClient

        client = TestClient(test_app)

        # Create test OTLP request
        request = trace_service_pb2.ExportTraceServiceRequest()

        # Add resource spans
        resource_spans = request.resource_spans.add()

        # Add resource attributes
        resource = resource_spans.resource
        attr = resource.attributes.add()
        attr.key = "service.name"
        attr.value.string_value = "test-service"

        # Add scope spans
        scope_spans = resource_spans.scope_spans.add()

        # Add span
        span = scope_spans.spans.add()
        span.name = "test-operation"
        span.trace_id = uuid4().bytes
        span.span_id = uuid4().bytes
        span.kind = trace_pb2.Span.SpanKind.SPAN_KIND_INTERNAL
        span.start_time_unix_nano = int(datetime.now().timestamp() * 1_000_000_000)
        span.end_time_unix_nano = int(datetime.now().timestamp() * 1_000_000_000)
        span.status.code = trace_pb2.Status.StatusCode.STATUS_CODE_OK

        # Add span attributes
        attr = span.attributes.add()
        attr.key = "input.prompt"
        attr.value.string_value = "test prompt"

        attr = span.attributes.add()
        attr.key = "output.response"
        attr.value.string_value = "test response"

        # Send request
        response = client.post(
            "/v1/traces/", content=request.SerializeToString(), headers={"Content-Type": "application/x-protobuf"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["spans_processed"] == 1

        # Verify run was created in database
        run_repo = RunRepository()
        runs = await run_repo.get_root_runs(limit=10)
        assert len(runs) >= 1

        # Find our test run
        test_run = None
        for run in runs:
            if run.name == "test-operation":
                test_run = run
                break

        assert test_run is not None
        assert test_run.name == "test-operation"
        assert test_run.run_type == "internal"
        assert test_run.inputs == {"input.prompt": "test prompt"}
        assert test_run.outputs == {"output.response": "test response"}
        assert test_run.project_name == "test-service"

    def test_otlp_http_invalid_content_type(self, test_app):
        """Test OTLP HTTP with invalid content type."""
        from fastapi.testclient import TestClient

        client = TestClient(test_app)

        response = client.post("/v1/traces/", content=b"invalid data", headers={"Content-Type": "text/plain"})

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported content type" in data["detail"]

    def test_otlp_http_invalid_protobuf(self, test_app):
        """Test OTLP HTTP with invalid protobuf data."""
        from fastapi.testclient import TestClient

        client = TestClient(test_app)

        response = client.post(
            "/v1/traces/", content=b"invalid protobuf data", headers={"Content-Type": "application/x-protobuf"}
        )

        assert response.status_code == 500
