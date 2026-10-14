from __future__ import annotations

import base64
import json
import threading
import time
from pathlib import Path
from typing import Any, Iterable

import anywidget
import traitlets

_OTLP_KINDS = ["unspecified", "internal", "server", "client", "producer", "consumer"]
_OTLP_STATUSES = ["unset", "ok", "error"]


def _json_safe(value: Any) -> Any:
    """Turn OTel attribute values (tuples, bytes, ...) into JSON-friendly ones."""
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, bytes):
        return value.hex()
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _otlp_value(value: dict[str, Any]) -> Any:
    """Decode an OTLP/JSON ``AnyValue`` (``{"stringValue": "x"}`` and friends)."""
    if "stringValue" in value:
        return value["stringValue"]
    if "boolValue" in value:
        return value["boolValue"]
    if "intValue" in value:
        return int(value["intValue"])  # int64 is encoded as a string in OTLP/JSON
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "arrayValue" in value:
        return [_otlp_value(v) for v in value["arrayValue"].get("values", [])]
    if "kvlistValue" in value:
        return _otlp_attributes(value["kvlistValue"].get("values", []))
    if "bytesValue" in value:
        return value["bytesValue"]
    return None


def _otlp_attributes(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    return {item["key"]: _otlp_value(item.get("value", {})) for item in items or []}


def _otlp_id(raw: str | None) -> str | None:
    """OTLP/JSON ids are hex, but some exporters emit base64 — normalize to hex."""
    if not raw:
        return None
    try:
        int(raw, 16)
        return raw.lower()
    except ValueError:
        return base64.b64decode(raw).hex()


def _otlp_enum(raw: Any, names: list[str], prefix: str) -> str:
    """Kinds/status codes arrive as ints (``2``) or names (``"SPAN_KIND_SERVER"``)."""
    if isinstance(raw, int):
        return names[raw] if 0 <= raw < len(names) else names[0]
    if isinstance(raw, str) and raw:
        return raw.removeprefix(prefix).lower()
    return names[0]


def _span_from_otlp(span: dict[str, Any], service: str | None) -> dict[str, Any]:
    end = span.get("endTimeUnixNano")
    status = span.get("status") or {}
    return {
        "span_id": _otlp_id(span.get("spanId")),
        "parent_id": _otlp_id(span.get("parentSpanId")),
        "trace_id": _otlp_id(span.get("traceId")),
        "name": span.get("name", ""),
        "service": service,
        "kind": _otlp_enum(span.get("kind"), _OTLP_KINDS, "SPAN_KIND_"),
        "start_ms": int(span.get("startTimeUnixNano", 0)) / 1e6,
        "end_ms": int(end) / 1e6 if end else None,
        "status": _otlp_enum(status.get("code"), _OTLP_STATUSES, "STATUS_CODE_"),
        "status_message": status.get("message", ""),
        "attributes": _otlp_attributes(span.get("attributes")),
        "events": [
            {
                "t_ms": int(event.get("timeUnixNano", 0)) / 1e6,
                "name": event.get("name", ""),
                "attributes": _otlp_attributes(event.get("attributes")),
            }
            for event in span.get("events") or []
        ],
        "links": [_otlp_id(link.get("spanId")) for link in span.get("links") or []],
    }


def spans_from_otlp(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one OTLP/JSON ``{"resourceSpans": [...]}`` document into span dicts."""
    out = []
    for resource_spans in doc.get("resourceSpans", []):
        resource = _otlp_attributes((resource_spans.get("resource") or {}).get("attributes"))
        service = resource.get("service.name")
        for scope_spans in resource_spans.get("scopeSpans", []):
            for span in scope_spans.get("spans", []):
                out.append(_span_from_otlp(span, service))
    return out


def span_to_dict(span: Any) -> dict[str, Any]:
    """Normalize an OpenTelemetry SDK span (``ReadableSpan`` or a live ``Span``)."""
    ctx = span.context
    resource = getattr(span, "resource", None)
    service = resource.attributes.get("service.name") if resource is not None else None
    status = span.status
    return {
        "span_id": format(ctx.span_id, "016x"),
        "parent_id": format(span.parent.span_id, "016x") if span.parent else None,
        "trace_id": format(ctx.trace_id, "032x"),
        "name": span.name,
        "service": service,
        "kind": span.kind.name.lower(),
        "start_ms": span.start_time / 1e6 if span.start_time else 0.0,
        "end_ms": span.end_time / 1e6 if span.end_time else None,
        "status": status.status_code.name.lower(),
        "status_message": status.description or "",
        "attributes": _json_safe(dict(span.attributes or {})),
        "events": [
            {
                "t_ms": event.timestamp / 1e6,
                "name": event.name,
                "attributes": _json_safe(dict(event.attributes or {})),
            }
            for event in span.events
        ],
        "links": [format(link.context.span_id, "016x") for link in span.links],
    }


class TraceView(anywidget.AnyWidget):
    """Waterfall viewer for OpenTelemetry traces, live or loaded from a file.

    Each span is one row: a tree gutter shows parent/child structure, followed by
    the span's state, an optional progress bar, a timeline bar, and its duration.
    Click a row for its attributes and events; drag the replay scrubber (or press
    *Replay*) to watch the trace unfold.

    Live, in-process (requires ``opentelemetry-sdk``)::

        view = TraceView(title="agent run")
        provider.add_span_processor(view.span_processor())
        view

    From existing data (no OpenTelemetry install needed)::

        TraceView.from_otlp("traces.json")              # OTLP/JSON or JSON lines
        TraceView.from_spans(exporter.get_finished_spans())

    A span with numeric ``progress.done`` and ``progress.total`` attributes gets
    a progress bar.
    """

    _esm = Path(__file__).parent / "static" / "traceview.js"
    _css = Path(__file__).parent / "static" / "traceview.css"

    # Normalized spans: {span_id, parent_id, trace_id, name, service, kind,
    # start_ms, end_ms, status, status_message, attributes, events, links}.
    # Times are epoch milliseconds; end_ms is None while a span is running.
    spans = traitlets.List(default_value=[]).tag(sync=True)
    # Trace shown in the widget; "" follows the most recently started trace.
    trace_id = traitlets.Unicode("").tag(sync=True)
    selected_span_id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    # Replay position in ms since the trace started; None shows everything.
    cursor_ms = traitlets.Float(None, allow_none=True).tag(sync=True)
    collapsed = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    title = traitlets.Unicode("Trace").tag(sync=True)
    # height: 0 means grow to fit; a positive value caps the rows and scrolls.
    height = traitlets.Int(0).tag(sync=True)
    # Kernel clock (epoch ms) at the last sync, so running bars grow correctly
    # even when the browser clock differs from the kernel's.
    now_ms = traitlets.Float(0.0).tag(sync=True)
    # Minimum ms between live syncs; skipped updates go out with the next span.
    sync_throttle_ms = traitlets.Int(0)

    def __init__(
        self,
        spans: list[dict[str, Any]] | None = None,
        *,
        title: str = "Trace",
        height: int = 0,
        sync_throttle_ms: int = 0,
        **kwargs: Any,
    ) -> None:
        if height < 0:
            raise ValueError("height must be >= 0")
        if sync_throttle_ms < 0:
            raise ValueError("sync_throttle_ms must be >= 0")
        spans = list(spans or [])
        super().__init__(
            spans=spans,
            title=title,
            height=height,
            sync_throttle_ms=sync_throttle_ms,
            now_ms=time.time() * 1000,
            **kwargs,
        )
        self._lock = threading.Lock()
        self._by_id: dict[str, dict[str, Any]] = {s["span_id"]: s for s in spans}
        # SDK spans that haven't ended yet; re-read on every sync so attribute
        # changes (like progress) made while they run show up.
        self._running: dict[str, Any] = {}
        self._last_sync = 0.0

    @classmethod
    def from_otlp(
        cls, source: str | Path | dict[str, Any] | list[dict[str, Any]], **kwargs: Any
    ) -> "TraceView":
        """Load OTLP/JSON: a file path (a JSON document or JSON lines), a dict, or a list of dicts."""
        if isinstance(source, (str, Path)):
            text = Path(source).read_text()
            try:
                docs = [json.loads(text)]
            except json.JSONDecodeError:  # the OTLP file exporter writes one doc per line
                docs = [json.loads(line) for line in text.splitlines() if line.strip()]
        elif isinstance(source, dict):
            docs = [source]
        else:
            docs = list(source)
        spans = [span for doc in docs for span in spans_from_otlp(doc)]
        return cls(spans, **kwargs)

    @classmethod
    def from_spans(cls, spans: Iterable[Any], **kwargs: Any) -> "TraceView":
        """Build from OpenTelemetry SDK spans, e.g. ``InMemorySpanExporter.get_finished_spans()``."""
        return cls([span_to_dict(span) for span in spans], **kwargs)

    def span_processor(self) -> Any:
        """An OpenTelemetry ``SpanProcessor`` that streams spans into this widget.

        Add it to a ``TracerProvider`` with ``provider.add_span_processor(...)``.
        Updates are sent from the thread that starts or ends a span; spans that
        finish on background threads appear with the next update from the
        notebook's own thread.
        """
        from opentelemetry.sdk.trace import SpanProcessor

        view = self

        class TraceViewProcessor(SpanProcessor):
            def on_start(self, span: Any, parent_context: Any = None) -> None:
                view._record(span)

            def on_end(self, span: Any) -> None:
                view._record(span)

        return TraceViewProcessor()

    def add_spans(self, spans: Iterable[Any]) -> None:
        """Add (or update, by ``span_id``) OpenTelemetry SDK spans or span dicts."""
        with self._lock:
            for span in spans:
                data = span if isinstance(span, dict) else span_to_dict(span)
                self._by_id[data["span_id"]] = data
        self._sync()

    def clear(self) -> None:
        """Drop all spans and reset the selection, replay cursor, and collapsed rows."""
        with self._lock:
            self._by_id = {}
            self._running = {}
        self.spans = []
        self.trace_id = ""
        self.selected_span_id = None
        self.cursor_ms = None
        self.collapsed = []

    @property
    def selected_span(self) -> dict[str, Any] | None:
        """The span dict of the clicked row, or ``None``."""
        for span in self.spans:
            if span["span_id"] == self.selected_span_id:
                return span
        return None

    def _record(self, span: Any) -> None:
        data = span_to_dict(span)
        with self._lock:
            self._by_id[data["span_id"]] = data
            if data["end_ms"] is None:
                self._running[data["span_id"]] = span
            else:
                self._running.pop(data["span_id"], None)
        if time.monotonic() - self._last_sync >= self.sync_throttle_ms / 1000:
            self._sync()

    def _sync(self) -> None:
        with self._lock:
            for span_id, span in self._running.items():
                self._by_id[span_id] = span_to_dict(span)
            spans = list(self._by_id.values())
        self._last_sync = time.monotonic()
        self.now_ms = time.time() * 1000
        self.spans = spans
