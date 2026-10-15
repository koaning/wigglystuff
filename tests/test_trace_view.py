import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import weave
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from weave.trace.box import box
from weave.trace.context import weave_client_context
from weave.trace.weave_client import WeaveClient

from wigglystuff import TraceView

OTLP_DOC = {
    "resourceSpans": [
        {
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "api"}}]},
            "scopeSpans": [
                {
                    "spans": [
                        {
                            "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                            "spanId": "00f067aa0ba902b7",
                            "name": "GET /orders",
                            "kind": "SPAN_KIND_SERVER",
                            "startTimeUnixNano": "1000000000",
                            "endTimeUnixNano": "1250000000",
                            "attributes": [
                                {"key": "http.status_code", "value": {"intValue": "500"}},
                                {"key": "tags", "value": {"arrayValue": {"values": [{"stringValue": "a"}]}}},
                            ],
                            "events": [{"timeUnixNano": "1200000000", "name": "exception", "attributes": []}],
                            "status": {"code": 2, "message": "boom"},
                        },
                        {
                            # base64 ids, as some protobuf->JSON exporters write them
                            "traceId": "S/kvNXezTaajzpKdDg5HNg==",
                            "spanId": "AAAAAAAAAAE=",
                            "parentSpanId": "APBnqgupArc=",
                            "name": "SELECT",
                            "kind": 3,
                            "startTimeUnixNano": "1010000000",
                            "endTimeUnixNano": "1100000000",
                            "links": [{"spanId": "00f067aa0ba902b7"}],
                        },
                    ]
                }
            ],
        }
    ]
}


def test_from_otlp_normalizes_spans():
    root, child = TraceView.from_otlp(OTLP_DOC).spans
    assert root["service"] == "api"
    assert root["kind"] == "server"
    assert root["status"] == "error" and root["status_message"] == "boom"
    assert root["start_ms"] == 1000.0 and root["end_ms"] == 1250.0
    assert root["attributes"] == {"http.status_code": 500, "tags": ["a"]}
    assert root["events"][0]["t_ms"] == 1200.0
    assert child["trace_id"] == root["trace_id"]
    assert child["parent_id"] == root["span_id"]
    assert child["kind"] == "client" and child["status"] == "unset"
    assert child["links"] == [root["span_id"]]


def test_from_otlp_reads_json_and_json_lines(tmp_path):
    doc = tmp_path / "trace.json"
    doc.write_text(json.dumps(OTLP_DOC))
    lines = tmp_path / "trace.jsonl"
    lines.write_text(json.dumps(OTLP_DOC) + "\n\n" + json.dumps(OTLP_DOC) + "\n")
    assert len(TraceView.from_otlp(doc).spans) == 2
    assert len(TraceView.from_otlp(str(lines)).spans) == 4
    assert len(TraceView.from_otlp([OTLP_DOC, OTLP_DOC]).spans) == 4


def test_selected_span_clear_and_validation():
    view = TraceView.from_otlp(OTLP_DOC)
    assert view.selected_span is None
    view.selected_span_id = "00f067aa0ba902b7"
    assert view.selected_span["name"] == "GET /orders"
    view.clear()
    assert view.spans == [] and view.selected_span_id is None
    with pytest.raises(ValueError):
        TraceView(height=-1)
    with pytest.raises(ValueError):
        TraceView(sync_throttle_ms=-1)


def test_span_processor_streams_running_and_ended_spans():

    view = TraceView()
    provider = TracerProvider(resource=Resource.create({"service.name": "demo"}))
    provider.add_span_processor(view.span_processor())
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("root"):
        with tracer.start_as_current_span("child") as child:
            child.set_attribute("progress.done", 1)
            assert [s["end_ms"] for s in view.spans] == [None, None]
            child.set_attribute("progress.done", 2)
        # the still-running root is re-read on every sync
        assert view.spans[1]["attributes"] == {"progress.done": 2}
        assert view.spans[1]["end_ms"] is not None

    root, child = view.spans
    assert root["end_ms"] is not None and root["service"] == "demo"
    assert child["parent_id"] == root["span_id"]

    # from_spans/add_spans take the SDK's finished spans too
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with tracer.start_as_current_span("again"):
        pass
    loaded = TraceView.from_spans(exporter.get_finished_spans())
    assert [s["name"] for s in loaded.spans] == ["again"]
    loaded.add_spans(exporter.get_finished_spans())
    assert len(loaded.spans) == 1  # same span_id is updated, not duplicated


@pytest.fixture
def weave_client():
    """A real WeaveClient whose trace server is a mock, so no W&B login is needed."""
    server = MagicMock()
    for method in ("obj_create", "file_create", "table_create"):
        getattr(server, method).return_value.digest = "abc123"
    client = WeaveClient("entity", "project", server, ensure_project_exists=False)
    weave_client_context.set_weave_client_global(client)
    yield client
    weave_client_context.set_weave_client_global(None)


def test_from_weave_normalizes_calls():
    failed = {
        "id": "c2",
        "parent_id": "c1",
        "trace_id": "t1",
        "op_name": "weave:///acme/bot/op/lookup_order:Hx3kQ9",
        "display_name": None,
        "started_at": "2026-10-14T09:00:01.000Z",
        "ended_at": "2026-10-14T09:00:01.500Z",
        "inputs": {"order_id": 1042},
        "exception": '{"type": "TimeoutError", "message": "slow", "traceback": [{"filename": "bot.py", "line_number": 3, "function_name": "lookup_order", "text": "raise TimeoutError"}]}',
        "summary": {"weave": {"status": "error"}, "status_counts": {}, "usage": {"m": {"prompt_tokens": 5}}},
        "attributes": {"weave": {"os": "mac"}, "env": "prod"},
    }
    # client.get_calls() hands back boxed values (BoxedStr ids, BoxedInt inputs, ...)
    running = SimpleNamespace(
        id=box("c1"), parent_id=None, trace_id=box("t1"), op_name="weave:///acme/bot/op/answer:abc",
        display_name="Answer ticket", started_at=box(datetime(2026, 10, 14, 9, tzinfo=timezone.utc)), ended_at=None,
        inputs={"attempt": box(1)}, output=None, exception=None, summary=None, attributes=None,
    )
    root, child = TraceView.from_weave([running, failed]).spans

    assert type(root["span_id"]) is str and type(root["trace_id"]) is str
    assert type(root["attributes"]["inputs"]["attempt"]) is int
    assert root["name"] == "Answer ticket" and root["end_ms"] is None and root["status"] == "ok"
    assert child["name"] == "lookup_order" and child["parent_id"] == "c1"
    assert child["end_ms"] - child["start_ms"] == 500
    assert child["status"] == "error" and child["status_message"] == "TimeoutError: slow"
    assert 'File "bot.py", line 3' in child["events"][0]["attributes"]["exception.stacktrace"]
    assert child["attributes"]["summary"] == {"usage": {"m": {"prompt_tokens": 5}}}
    assert child["attributes"]["env"] == "prod" and "weave" not in child["attributes"]


def test_capture_weave_records_only_calls_inside_the_block(weave_client):
    @weave.op
    def child(x: int) -> int:
        if x == 2:
            raise ValueError("nope")
        return x

    @weave.op
    def parent(n: int) -> list:
        return [child(i) for i in range(n)]

    view = TraceView()
    parent(1)
    with view.capture_weave():
        result, call = parent.call(2)
    parent(1)

    assert result == [0, 1]
    root, *children = view.spans
    assert root["span_id"] == call.id and root["name"] == "parent"
    assert [c["parent_id"] for c in children] == [call.id, call.id]
    assert all(s["end_ms"] is not None for s in view.spans)

    with pytest.raises(ValueError), view.capture_weave():
        parent(3)
    assert [s["status_message"] for s in view.spans if s["status"] == "error"] == ["ValueError: nope"] * 2

    n_spans = len(view.spans)
    parent(1)  # the client is unhooked again, even after an error
    assert len(view.spans) == n_spans

    weave_client_context.set_weave_client_global(None)
    with pytest.raises(RuntimeError), view.capture_weave():
        pass
