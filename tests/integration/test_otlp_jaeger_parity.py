import os
import time
from typing import Any

import pytest
import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

AGENT_SPY_BASE = os.getenv("AGENT_SPY_BASE", "http://localhost:8000").rstrip("/")
JAEGER_QUERY_URL = os.getenv("JAEGER_QUERY_URL", "http://dev-container-jaeger:16686").rstrip("/")


def _fetch_agent_spy_workflow_by_name(base_url: str, workflow_name: str) -> dict[str, Any] | None:
    resp = requests.get(f"{base_url}/api/v1/runs", params={"limit": 500}, timeout=10)
    if resp.status_code != 200:
        return None
    runs = resp.json()
    roots = [r for r in runs if not r.get("parent_run_id") and r.get("name") == workflow_name]
    roots.sort(key=lambda r: r.get("start_time") or "", reverse=True)
    if not roots:
        return None
    root = roots[0]
    rid = root["id"]
    name = root["name"]
    hier_resp = requests.get(f"{base_url}/api/v1/dashboard/runs/{rid}/hierarchy", timeout=10)
    if hier_resp.status_code != 200:
        return None
    hier = hier_resp.json()

    def walk(node: dict[str, Any] | None, names: list[str]) -> None:
        if not node:
            return
        nm = node.get("name")
        if nm:
            names.append(nm)
        for c in node.get("children") or []:
            walk(c, names)

    names: list[str] = []
    walk(hier.get("hierarchy"), names)
    return {"name": name, "root_id": rid, "total": hier.get("total_runs"), "names": names}


def _fetch_jaeger_trace(jq_url: str, workflow_name: str) -> dict[str, Any] | None:
    params = {"service": "agent-spy-forwarder", "lookback": "30m", "limit": 200}
    resp = requests.get(f"{jq_url}/api/traces", params=params, timeout=10)
    if resp.status_code != 200:
        return None
    js = resp.json()
    best = None
    best_ts = -1
    for tr in js.get("data") or []:
        spans = tr.get("spans") or []
        if not any(s.get("operationName") == workflow_name for s in spans):
            continue
        ts = max((s.get("startTime") or 0) for s in spans) if spans else 0
        if ts > best_ts:
            best_ts = ts
            best = tr
    if not best:
        return None
    spans = best.get("spans") or []
    ops = sorted({s.get("operationName") for s in spans if s.get("operationName")})
    # Build parent->children mapping by names
    id2name = {s.get("spanID"): s.get("operationName") for s in spans}
    parent_children: dict[str | None, list[str]] = {}
    for s in spans:
        parent_name = None
        for ref in s.get("references") or []:
            if ref.get("refType") == "CHILD_OF":
                parent_name = id2name.get(ref.get("spanID"))
                break
        parent_children.setdefault(parent_name, []).append(s.get("operationName"))
    return {"traceID": best.get("traceID"), "count": len(spans), "ops": ops, "tree": parent_children}


def _emit_workflow_via_otlp(base_url: str, workflow_name: str, step_suffix: str) -> None:
    # Configure a fresh tracer provider with HTTP exporter to Agent Spy
    resource = Resource.create({"service.name": "agent-spy-parity-test"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{base_url}/v1/traces/")
    processor = BatchSpanProcessor(exporter, max_queue_size=100, max_export_batch_size=32)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)

    # Build 9-span workflow: root + 4 steps + 4 llm/chat children
    with tracer.start_as_current_span(workflow_name):
        with tracer.start_as_current_span("story_concept_generation"), tracer.start_as_current_span(
            f"ollama_generate_{step_suffix}"
        ):
            pass
        with tracer.start_as_current_span("character_development"), tracer.start_as_current_span("ollama_chat"):
            pass
        with tracer.start_as_current_span("opening_scene_writing"), tracer.start_as_current_span(
            f"ollama_generate_{step_suffix}"
        ):
            pass
        with tracer.start_as_current_span("story_outline_creation"), tracer.start_as_current_span("ollama_chat"):
            pass

    # Force flush to send to Agent Spy
    provider.force_flush(timeout_millis=30000)


def _services_available() -> bool:
    try:
        r1 = requests.get(f"{AGENT_SPY_BASE}/health", timeout=5)
        r2 = requests.get(f"{JAEGER_QUERY_URL}/", timeout=5)
        return r1.status_code == 200 and r2.status_code < 500
    except Exception:
        return False


@pytest.mark.integration
def test_creative_workflow_jaeger_parity() -> None:
    if not _services_available():
        pytest.skip("Agent Spy or Jaeger not available; skipping parity test")

    # Emit a deterministic, isolated workflow via OTLP
    unique = str(int(time.time()))
    workflow_name = f"creative_writing_workflow_test-{unique}"
    _emit_workflow_via_otlp(AGENT_SPY_BASE, workflow_name, unique)

    # Allow forwarder debounce and DB persistence
    deadline = time.time() + 20
    agent = None
    while time.time() < deadline and not agent:
        agent = _fetch_agent_spy_workflow_by_name(AGENT_SPY_BASE, workflow_name)
        if not agent:
            time.sleep(1)
    assert agent, "Emitted workflow not found in Agent Spy"

    jae = None
    deadline = time.time() + 30
    while time.time() < deadline and not jae:
        jae = _fetch_jaeger_trace(JAEGER_QUERY_URL, workflow_name)
        if not jae:
            time.sleep(2)
    assert jae, "Jaeger trace not found for emitted workflow"

    assert jae["count"] == agent["total"], f"Jaeger span count {jae['count']} != AgentSpy total {agent['total']}"

    # All Agent Spy node names should appear as Jaeger operation names
    missing = [n for n in agent["names"] if n not in jae["ops"]]
    assert not missing, f"Missing span names in Jaeger: {missing}"

    # Root should be present under the None/null parent in Jaeger tree
    roots = jae["tree"].get(None) or jae["tree"].get("null") or []
    assert workflow_name in roots, "Root workflow name not present as Jaeger root"
