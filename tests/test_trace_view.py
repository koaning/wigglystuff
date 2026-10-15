import json

import pytest

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
    pytest.importorskip("opentelemetry.sdk")
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

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
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with tracer.start_as_current_span("again"):
        pass
    loaded = TraceView.from_spans(exporter.get_finished_spans())
    assert [s["name"] for s in loaded.spans] == ["again"]
    loaded.add_spans(exporter.get_finished_spans())
    assert len(loaded.spans) == 1  # same span_id is updated, not duplicated


class _Boxed(str):
    """Stands in for weave's BoxedStr: a str subclass that must not leak to the browser."""


def test_from_weave_normalizes_calls():
    from datetime import datetime, timezone
    from types import SimpleNamespace

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
    running = SimpleNamespace(
        id=_Boxed("c1"), parent_id=None, trace_id=_Boxed("t1"), op_name="weave:///acme/bot/op/answer:abc",
        display_name="Answer ticket", started_at=datetime(2026, 10, 14, 9, tzinfo=timezone.utc), ended_at=None,
        inputs={}, output=None, exception=None, summary=None, attributes=None,
    )
    root, child = TraceView.from_weave([running, failed]).spans

    assert type(root["span_id"]) is str and type(root["trace_id"]) is str
    assert root["name"] == "Answer ticket" and root["end_ms"] is None and root["status"] == "ok"
    assert child["name"] == "lookup_order" and child["parent_id"] == "c1"
    assert child["end_ms"] - child["start_ms"] == 500
    assert child["status"] == "error" and child["status_message"] == "TimeoutError: slow"
    assert 'File "bot.py", line 3' in child["events"][0]["attributes"]["exception.stacktrace"]
    assert child["attributes"]["summary"] == {"usage": {"m": {"prompt_tokens": 5}}}
    assert child["attributes"]["env"] == "prod" and "weave" not in child["attributes"]


def test_capture_weave_records_only_calls_inside_the_block(monkeypatch):
    import sys
    from datetime import datetime, timezone
    from types import SimpleNamespace

    class FakeClient:
        def create_call(self, op, inputs, parent=None):
            return SimpleNamespace(
                id=f"c{len(inputs)}{op}", parent_id=parent, trace_id="t", op_name=op, display_name=None,
                started_at=datetime.now(timezone.utc), ended_at=None, inputs=inputs, output=None,
                exception=None, summary={}, attributes={},
            )

        def finish_call(self, call, output=None, exception=None):
            call.ended_at, call.output = datetime.now(timezone.utc), output
            call.exception = repr(exception) if exception else None

    client = FakeClient()
    monkeypatch.setitem(sys.modules, "weave", SimpleNamespace(get_client=lambda: client))

    def op(name):
        client.finish_call(client.create_call(name, {}), output=name)

    view = TraceView()
    op("before")
    with view.capture_weave():
        op("inside")
        assert view.spans[0]["end_ms"] is not None
    op("after")
    assert [s["name"] for s in view.spans] == ["inside"]

    with pytest.raises(ValueError), view.capture_weave():
        client.create_call("boom", {})
        raise ValueError("boom")
    assert view.spans[-1]["end_ms"] is None  # started, never finished
    assert "create_call" not in vars(client) or vars(client)["create_call"].__func__ is FakeClient.create_call

    monkeypatch.setitem(sys.modules, "weave", SimpleNamespace(get_client=lambda: None))
    with pytest.raises(RuntimeError), view.capture_weave():
        pass
