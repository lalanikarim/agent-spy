"""Unit tests for OpenTelemetry converter."""

from datetime import datetime
from uuid import UUID, uuid4

from src.otel.receiver.converter import OtlpToAgentSpyConverter
from src.otel.receiver.models import OtlpSpan
from src.otel.utils.mapping import map_run_type_to_span_kind, map_span_kind_to_run_type


class TestOtlpConverter:
    """Test OTLP to Agent Spy conversion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = OtlpToAgentSpyConverter()
        self.test_span_id = str(uuid4())
        self.test_trace_id = str(uuid4())

    def test_convert_basic_span(self):
        """Test basic span conversion."""
        # Create test span
        span = OtlpSpan(
            trace_id=self.test_trace_id,
            span_id=self.test_span_id,
            parent_span_id=None,
            name="test-operation",
            kind=1,  # INTERNAL
            start_time=datetime.now(),
            end_time=datetime.now(),
            attributes={"service.name": "test-service"},
            events=[],
            links=[],
            status={"code": 1},  # OK
            resource={"service.name": "test-service"},
        )

        # Convert to Agent Spy run
        run = self.converter.convert_span(span, span.resource)

        # Verify conversion
        assert run.id == UUID(self.test_span_id)
        assert run.name == "test-operation"
        assert run.run_type == "internal"
        assert run.project_name == "test-service"
        assert run.parent_run_id is None

    def test_convert_span_with_parent(self):
        """Test span conversion with parent."""
        parent_span_id = str(uuid4())

        span = OtlpSpan(
            trace_id=self.test_trace_id,
            span_id=self.test_span_id,
            parent_span_id=parent_span_id,
            name="child-operation",
            kind=3,  # CLIENT
            start_time=datetime.now(),
            end_time=datetime.now(),
            attributes={"input.prompt": "test prompt"},
            events=[],
            links=[],
            status={"code": 1},
            resource={"service.name": "test-service"},
        )

        run = self.converter.convert_span(span, span.resource)

        assert run.parent_run_id == UUID(parent_span_id)
        assert run.run_type == "client"
        assert run.inputs == {"input.prompt": "test prompt"}

    def test_convert_failed_span(self):
        """Test conversion of failed span."""
        span = OtlpSpan(
            trace_id=self.test_trace_id,
            span_id=self.test_span_id,
            parent_span_id=None,
            name="failed-operation",
            kind=2,  # SERVER
            start_time=datetime.now(),
            end_time=datetime.now(),
            attributes={},
            events=[],
            links=[],
            status={"code": 2, "message": "Operation failed"},  # ERROR
            resource={"service.name": "test-service"},
        )

        run = self.converter.convert_span(span, span.resource)

        assert run.error == "Operation failed"
        assert run.run_type == "server"

    def test_extract_inputs_outputs(self):
        """Test extraction of inputs and outputs from attributes."""
        span = OtlpSpan(
            trace_id=self.test_trace_id,
            span_id=self.test_span_id,
            parent_span_id=None,
            name="test-operation",
            kind=1,
            start_time=datetime.now(),
            end_time=datetime.now(),
            attributes={"input.prompt": "test prompt", "output.response": "test response", "other.attr": "other value"},
            events=[],
            links=[],
            status={"code": 1},
            resource={"service.name": "test-service"},
        )

        run = self.converter.convert_span(span, span.resource)

        assert run.inputs == {"input.prompt": "test prompt"}
        assert run.outputs == {"output.response": "test response"}

    def test_extract_project_name(self):
        """Test extraction of project name from resource."""
        span = OtlpSpan(
            trace_id=self.test_trace_id,
            span_id=self.test_span_id,
            parent_span_id=None,
            name="test-operation",
            kind=1,
            start_time=datetime.now(),
            end_time=datetime.now(),
            attributes={},
            events=[],
            links=[],
            status={"code": 1},
            resource={"service.name": "my-service", "deployment.environment": "production"},
        )

        run = self.converter.convert_span(span, span.resource)

        assert run.project_name == "my-service"

    def test_convert_events(self):
        """Test conversion of span events."""
        span = OtlpSpan(
            trace_id=self.test_trace_id,
            span_id=self.test_span_id,
            parent_span_id=None,
            name="test-operation",
            kind=1,
            start_time=datetime.now(),
            end_time=datetime.now(),
            attributes={},
            events=[{"name": "event1", "time_unix_nano": 1234567890, "attributes": {"key1": "value1"}}],
            links=[],
            status={"code": 1},
            resource={"service.name": "test-service"},
        )

        run = self.converter.convert_span(span, span.resource)

        assert run.events is not None
        assert len(run.events) == 1
        assert run.events[0]["name"] == "event1"
        assert run.events[0]["attributes"] == {"key1": "value1"}


class TestMappingFunctions:
    """Test mapping utility functions."""

    def test_map_span_kind_to_run_type(self):
        """Test span kind to run type mapping."""
        assert map_span_kind_to_run_type(0) == "internal"  # UNSPECIFIED
        assert map_span_kind_to_run_type(1) == "internal"  # INTERNAL
        assert map_span_kind_to_run_type(2) == "server"  # SERVER
        assert map_span_kind_to_run_type(3) == "client"  # CLIENT
        assert map_span_kind_to_run_type(4) == "producer"  # PRODUCER
        assert map_span_kind_to_run_type(5) == "consumer"  # CONSUMER
        assert map_span_kind_to_run_type(99) == "custom"  # Unknown

    def test_map_run_type_to_span_kind(self):
        """Test run type to span kind mapping."""
        assert map_run_type_to_span_kind("chain") == 1  # INTERNAL
        assert map_run_type_to_span_kind("llm") == 3  # CLIENT
        assert map_run_type_to_span_kind("tool") == 3  # CLIENT
        assert map_run_type_to_span_kind("server") == 2  # SERVER
        assert map_run_type_to_span_kind("client") == 3  # CLIENT
        assert map_run_type_to_span_kind("unknown") == 0  # UNSPECIFIED
