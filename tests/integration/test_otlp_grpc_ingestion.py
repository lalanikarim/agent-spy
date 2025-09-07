import asyncio

import grpc
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2_grpc import TraceServiceStub
from opentelemetry.proto.resource.v1.resource_pb2 import Resource
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span


def _build_minimal_request(service_name: str, span_name: str) -> ExportTraceServiceRequest:
    req = ExportTraceServiceRequest()
    rs = req.resource_spans.add()

    if rs.resource is None:
        rs.resource = Resource()
    attr = rs.resource.attributes.add()
    attr.key = "service.name"
    attr.value.string_value = service_name

    ss = rs.scope_spans.add()
    sp = ss.spans.add()
    sp.name = span_name
    sp.trace_id = bytes.fromhex("0" * 32)
    sp.span_id = bytes.fromhex("0" * 16)
    sp.start_time_unix_nano = 1_000_000_000
    sp.end_time_unix_nano = 2_000_000_000
    return req


def test_grpc_ingestion_basic():
    # Assumes server is running with gRPC enabled on 127.0.0.1:4317
    channel = grpc.insecure_channel("127.0.0.1:4317")
    stub = TraceServiceStub(channel)
    req = _build_minimal_request("it-grpc-service", "it-span")
    # Will raise on non-OK
    stub.Export(req)

