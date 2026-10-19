# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anywidget",
#     "marimo",
#     "opentelemetry-sdk",
#     "wigglystuff==0.5.35",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import TraceView

    return TraceView, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## TraceView

    A waterfall for **OpenTelemetry traces**. Every span is a row: the gutter on
    the left draws the parent → child tree, followed by the span's state, a
    timeline bar, and its duration. Click a row to see its attributes and
    events, fold subtrees with `−`, and press **Replay** (or drag the scrubber)
    to watch the trace unfold.

    ### Live, in-process

    `view.span_processor()` is an OTel `SpanProcessor`: add it to a
    `TracerProvider` once, and from then on every
    `with tracer.start_as_current_span(...)` block made through that provider
    streams into the widget as spans start and end. The cell below runs a fake
    research agent — rerun it to get another trace, then use the dropdown to
    switch between runs.
    """)
    return


@app.cell
def _(TraceView):
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    live_view = TraceView(title="research_agent")
    provider = TracerProvider(resource=Resource.create({"service.name": "research-agent"}))
    provider.add_span_processor(live_view.span_processor())
    tracer = provider.get_tracer("demo")
    return live_view, tracer


@app.cell(expand_output=True)
def _(live_view, mo):
    run_agent = mo.ui.run_button(label="Run the agent again")
    mo.vstack([live_view, run_agent])
    return (run_agent,)


@app.cell
def _(fake_llm, tracer):
    with tracer.start_as_current_span("agent.run") as _run:
        fake_llm(
            "llm.answer",
            "Summarize growth per capital.",
            "Dublin, Madrid and Warsaw grew fastest; Riga and Vilnius shrank.",
            1.0,
        )
    return


@app.cell(hide_code=True)
def _(run_agent, tracer):
    import time

    run_agent.value  # rerun this cell on click

    def fake_llm(name, prompt, answer, seconds):
        with tracer.start_as_current_span(name) as span:
            span.set_attribute("gen_ai.request.model", "claude-sonnet-5-5")
            span.set_attribute("gen_ai.prompt", prompt)
            time.sleep(seconds)
            span.add_event("message", {"message": answer})
            span.set_attribute("gen_ai.completion", answer)
            span.set_attribute("gen_ai.usage.input_tokens", 812)
            span.set_attribute("gen_ai.usage.output_tokens", len(answer.split()) * 3)

    with tracer.start_as_current_span("agent.run") as run:
        question = "Which European capitals grew fastest since 2000?"
        run.set_attribute("input.question", question)
        fake_llm("llm.plan", question, "Search population data, then compare growth.", 0.7)

        with tracer.start_as_current_span("tool.search_docs") as search:
            search.set_attribute("query", "european capital population 2000 2024")
            time.sleep(0.5)
            search.set_attribute("results", 24)

        with tracer.start_as_current_span("embed_documents") as embed:
            embed.set_attribute("progress.total", 24)
            for batch in range(4):
                with tracer.start_as_current_span("embed.batch") as b:
                    b.set_attribute("batch", batch)
                    time.sleep(0.3)
                embed.set_attribute("progress.done", (batch + 1) * 6)

        try:
            with tracer.start_as_current_span("tool.fetch_url") as fetch:
                fetch.set_attribute("url", "https://ec.europa.eu/eurostat/…")
                time.sleep(0.6)
                raise TimeoutError("eurostat did not answer within 600ms")
        except TimeoutError:
            run.add_event("retry", {"message": "fetch_url timed out, retrying once"})

        with tracer.start_as_current_span("tool.fetch_url") as fetch:
            fetch.set_attribute("url", "https://ec.europa.eu/eurostat/…")
            fetch.set_attribute("attempt", 2)
            time.sleep(0.4)

        fake_llm(
            "llm.answer",
            "Summarize growth per capital.",
            "Dublin, Madrid and Warsaw grew fastest; Riga and Vilnius shrank.",
            1.0,
        )
    return (fake_llm,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Concurrent work

    Nothing extra is needed for asyncio: spans started inside tasks keep their
    parent through `contextvars`, so a fan-out shows up as overlapping bars
    under one parent. This cell fetches three sources at once and then merges
    them; press the button to run it again.
    """)
    return


@app.cell
def _(TraceView):
    from opentelemetry.sdk.resources import Resource as _Resource
    from opentelemetry.sdk.trace import TracerProvider as _TracerProvider

    fan_out_view = TraceView(title="gather_sources")
    fan_out_provider = _TracerProvider(resource=_Resource.create({"service.name": "research-agent"}))
    fan_out_provider.add_span_processor(fan_out_view.span_processor())
    fan_out_tracer = fan_out_provider.get_tracer("demo")
    return fan_out_tracer, fan_out_view


@app.cell(expand_output=True)
def _(fan_out_view, mo):
    run_fan_out = mo.ui.run_button(label="Fan out again")
    mo.vstack([fan_out_view, run_fan_out])
    return (run_fan_out,)


@app.cell(hide_code=True)
async def _(fan_out_tracer, run_fan_out):
    import asyncio

    run_fan_out.value  # rerun this cell on click

    async def fetch_source(source, seconds):
        with fan_out_tracer.start_as_current_span(f"fetch {source}") as span:
            span.set_attribute("source", source)
            await asyncio.sleep(seconds)
            with fan_out_tracer.start_as_current_span("parse"):
                await asyncio.sleep(0.15)

    with fan_out_tracer.start_as_current_span("gather_sources"):
        await asyncio.gather(fetch_source("eurostat", 0.6), fetch_source("worldbank", 1.1), fetch_source("un_data", 0.8))
        with fan_out_tracer.start_as_current_span("llm.merge"):
            await asyncio.sleep(0.5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Load existing traces

    `TraceView.from_otlp(...)` reads OTLP/JSON — a dict, a file, or the JSON
    lines written by the OpenTelemetry Collector's file exporter. No
    OpenTelemetry install needed. This one spans four services: the order email
    is sent from a queue consumer whose span *links* back to the producer
    (dashed curve). Wrapped in `mo.ui.anywidget`, the clicked span is
    available in Python.
    """)
    return


@app.cell(hide_code=True)
def _():
    T0 = 1_760_000_000_000_000_000  # epoch ns
    TRACE = "4bf92f3577b34da6a3ce929d0e0e4736"

    def span(span_id, parent, name, start_ms, end_ms, kind=1, error=None, attrs=None, events=None, links=None):
        return {
            "traceId": TRACE,
            "spanId": span_id,
            "parentSpanId": parent or "",
            "name": name,
            "kind": kind,
            "startTimeUnixNano": str(T0 + int(start_ms * 1e6)),
            "endTimeUnixNano": str(T0 + int(end_ms * 1e6)),
            "attributes": [{"key": k, "value": {"stringValue": str(v)}} for k, v in (attrs or {}).items()],
            "events": [
                {"timeUnixNano": str(T0 + int(t * 1e6)), "name": n, "attributes": [{"key": k, "value": {"stringValue": v}} for k, v in a.items()]}
                for t, n, a in events or []
            ],
            "links": [{"traceId": TRACE, "spanId": link} for link in links or []],
            "status": {"code": 2, "message": error} if error else {},
        }

    services = {
        "frontend": [
            span("a000000000000001", None, "POST /checkout", 0, 412, kind=2, attrs={"http.route": "/checkout", "http.response.status_code": 200}),
            span("a000000000000002", "a000000000000001", "render confirmation", 380, 410),
        ],
        "cart-service": [
            span("b000000000000001", "a000000000000001", "GetCart", 6, 58, kind=2),
            span("b000000000000002", "b000000000000001", "redis GET cart:42", 9, 13, kind=3, events=[(12, "cache_miss", {"key": "cart:42"})]),
            span("b000000000000003", "b000000000000001", "SELECT cart_items", 15, 52, kind=3, attrs={"db.system": "postgresql"}),
        ],
        "payment-service": [
            span("c000000000000001", "a000000000000001", "Charge", 62, 371, kind=2),
            span("c000000000000002", "c000000000000001", "POST stripe /charges", 66, 166, kind=3, error="card_declined: retrying with 3DS",
                 events=[(165, "exception", {"exception.type": "CardError", "exception.message": "card_declined"})]),
            span("c000000000000003", "c000000000000001", "POST stripe /charges", 175, 352, kind=3, attrs={"attempt": 2}),
            span("c000000000000004", "c000000000000001", "publish order.paid", 356, 364, kind=4),
        ],
        "email-service": [
            span("d000000000000001", None, "consume order.paid", 520, 545, kind=5, links=["c000000000000004"]),
            span("d000000000000002", "d000000000000001", "send receipt", 548, 790, kind=3, attrs={"email.template": "receipt"}),
        ],
    }
    otlp_doc = {
        "resourceSpans": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": name}}]},
                "scopeSpans": [{"scope": {"name": "demo"}, "spans": spans}],
            }
            for name, spans in services.items()
        ]
    }
    return (otlp_doc,)


@app.cell(expand_output=True)
def _(TraceView, mo, otlp_doc):
    loaded = mo.ui.anywidget(TraceView.from_otlp(otlp_doc, title="checkout"))
    loaded
    return (loaded,)


@app.cell(hide_code=True)
def _(loaded, mo):
    selected = loaded.widget.selected_span
    mo.md(
        f"Selected **{selected['name']}** from `{selected['service']}`: status `{selected['status']}`."
        if selected
        else "Click a row above to select a span."
    )
    return


if __name__ == "__main__":
    app.run()
