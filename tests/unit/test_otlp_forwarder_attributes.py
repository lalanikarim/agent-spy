import types

from src.otel.forwarder.config import OtlpForwarderConfig
from src.otel.forwarder.service import OtlpForwarderService


def _mock_run(**kwargs):
    obj = types.SimpleNamespace(**kwargs)
    return obj


def test_extract_attributes_minimal():
    cfg = OtlpForwarderConfig(enabled=False)
    svc = OtlpForwarderService(cfg)
    run = _mock_run(
        id="11111111-1111-1111-1111-111111111111",
        name="unit-run",
        run_type="chain",
        status="completed",
        project_name="unit-project",
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T00:00:01Z",
        inputs={},
        outputs={},
        tags=None,
        extra=None,
        trace_id="22222222-2222-2222-2222-222222222222",
        parent_run_id=None,
    )

    attrs = svc._extract_attributes(run)  # type: ignore
    assert attrs["run.id"] == str(run.id)
    assert attrs["run.type"] == run.run_type
    assert attrs["run.status"] == run.status
    assert attrs["project.name"] == run.project_name
    assert attrs["run.start_time"].startswith("2024-01-01T00:00:00")
    assert attrs["run.end_time"].startswith("2024-01-01T00:00:01")
    assert attrs["trace.id"] == str(run.trace_id)
    assert "parent_run.id" not in attrs


def test_extract_attributes_with_parent_and_data():
    cfg = OtlpForwarderConfig(enabled=False)
    svc = OtlpForwarderService(cfg)
    run = _mock_run(
        id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        name="unit-run",
        run_type="tool",
        status="completed",
        project_name="unit-project",
        start_time="2024-01-01T00:00:00+00:00",
        end_time="2024-01-01T00:00:03+00:00",
        inputs={"prompt": "hi"},
        outputs={"result": "ok"},
        tags=["t1", "t2"],
        extra={"k": "v"},
        trace_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        parent_run_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
    )

    attrs = svc._extract_attributes(run)  # type: ignore
    assert attrs["parent_run.id"] == str(run.parent_run_id)
    assert attrs["input.prompt"] == "hi"
    assert attrs["output.result"] == "ok"
    assert attrs["extra.k"] == "v"
    assert isinstance(attrs.get("run.tags"), list)
