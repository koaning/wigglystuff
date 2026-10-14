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
