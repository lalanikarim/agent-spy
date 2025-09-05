import gzip
import os

import httpx
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.resource.v1.resource_pb2 import Resource
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span


def _build_minimal_request(service_name: str, span_name: str) -> bytes:
    req = ExportTraceServiceRequest()
    rs = req.resource_spans.add()

    # Resource attributes: service.name
    if rs.resource is None:
        rs.resource = Resource()
    attr = rs.resource.attributes.add()
    attr.key = "service.name"
    attr.value.string_value = service_name

    ss = rs.scope_spans.add()
    sp = ss.spans.add()
    sp.name = span_name
    # Provide 16-byte trace id and 8-byte span id
    sp.trace_id = bytes.fromhex("0" * 32)
    sp.span_id = bytes.fromhex("0" * 16)
    sp.start_time_unix_nano = 1_000_000_000
    sp.end_time_unix_nano = 2_000_000_000
    return req.SerializeToString()


def _post(body: bytes, gzip_enabled: bool) -> httpx.Response:
    url = os.getenv("OTLP_HTTP_URL", "http://localhost:8000/v1/traces")
    headers = {"content-type": "application/x-protobuf"}
    data = body
    if gzip_enabled:
        headers["content-encoding"] = "gzip"
        data = gzip.compress(body)
    with httpx.Client(timeout=5.0) as client:
        return client.post(url, content=data, headers=headers)


def test_http_ingestion_plain_and_gzip():
    body = _build_minimal_request("it-http-service", "it-span")
    r1 = _post(body, gzip_enabled=False)
    assert r1.status_code in (200, 207), r1.text
    r2 = _post(body, gzip_enabled=True)
    assert r2.status_code in (200, 207), r2.text

