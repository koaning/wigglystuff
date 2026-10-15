# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anywidget",
#     "marimo",
#     "weave",
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
    ## TraceView × W&B Weave

    [Weave](https://weave-docs.wandb.ai/) records every `@weave.op` call as a
    *call* — inputs, output, exception, timing, parent call. `TraceView` can
    show those calls as a waterfall, either live while your code runs or loaded
    back from W&B afterwards.

    ### Live

    Call your `@weave.op` as usual, inside `with view.capture_weave():`.
    The calls made in that block stream into the widget as each op starts
    and ends, and still go to W&B as usual. This part needs a W&B account
    (`wandb login` or `WANDB_API_KEY`).
    """)
    return


@app.cell
def _(mo):
    project = mo.ui.text(label="W&B project", placeholder="entity/project or project")
    project
    return (project,)


@app.cell
def _(mo, project):
    import weave

    mo.stop(not project.value, mo.md("*Enter a W&B project above to connect.*"))
    client = weave.init(project.value)
    return client, weave


@app.cell(expand_output=True)
def _(TraceView, mo):
    live_view = TraceView(title="support_bot")
    run_bot = mo.ui.run_button(label="Answer another ticket")
    mo.vstack([live_view, run_bot])
    return (live_view,)


@app.cell
def _(weave):
    import time

    # A fake support bot: no LLM keys needed, the sleeps stand in for real work.
    @weave.op
    def call_llm(prompt: str, seconds: float) -> str:
        time.sleep(seconds)
        return "Look up the order, then answer." if "Plan" in prompt else "It ships tomorrow."

    @weave.op
    def lookup_order(order_id: int, attempt: int) -> dict:
        time.sleep(0.5)
        if attempt == 1:
            raise TimeoutError("orders-db did not answer within 500 ms")
        return {"order_id": order_id, "status": "packed", "ships": "tomorrow"}

    @weave.op
    def answer_ticket(ticket: str) -> str:
        call_llm(f"Plan how to answer: {ticket}", seconds=1.0)
        for attempt in (1, 2):
            try:
                order = lookup_order(1042, attempt=attempt)
                break
            except TimeoutError:
                pass
        return call_llm(f"Answer {ticket!r} using {order}", seconds=1.2)

    return (answer_ticket,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Seeing changes live

    You can use the `live_view.capture_weave()` context manager to view a call live in the widget.
    """)
    return


@app.cell(expand_output=True)
def _(live_view):
    live_view
    return


@app.cell
def _(answer_ticket, live_view):
    # Run this manually.
    with live_view.capture_weave():
        # .call() also returns the Call record, so the cell below knows which trace to load.
        _answer, root_call = answer_ticket.call("Where is my order #1042?")
    return (root_call,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Load a finished trace back from W&B

    `TraceView.from_weave(...)` takes what `client.get_calls(...)` returns, so
    any trace already stored in a project can be opened later — here, the run
    above.
    """)
    return


@app.cell(expand_output=True)
def _(TraceView, client, root_call):
    client.flush()  # make sure the calls above have reached the server
    calls = client.get_calls(filter={"trace_ids": [root_call.trace_id]})
    TraceView.from_weave(calls, title="support_bot (from W&B)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Without a W&B account

    `from_weave` also accepts plain dicts in the shape of the service API's
    call JSON, so this one runs offline. Click a row to see the call's inputs,
    output, and token usage, or the failed call's exception.
    """)
    return


@app.cell(expand_output=True)
def _(TraceView):
    def weave_call(call_id, parent, op, start_s, end_s, inputs, output=None, exception=None, usage=None):
        return {
            "id": call_id,
            "parent_id": parent,
            "trace_id": "0199e2a4-7c1f-7d3a-9b6e-5f0c2d8a1e47",
            "op_name": f"weave:///acme/support-bot/op/{op}:Hx3kQ9",
            "display_name": None,
            "started_at": f"2026-10-14T09:00:{start_s:06.3f}Z",
            "ended_at": f"2026-10-14T09:00:{end_s:06.3f}Z",
            "inputs": inputs,
            "output": output,
            "exception": exception,
            "summary": {"usage": usage} if usage else {},
        }

    timeout = '{"type": "TimeoutError", "message": "orders-db did not answer within 500 ms", "traceback": []}'
    weave_calls = [
        weave_call("c1", None, "answer_ticket", 0.0, 4.1, {"ticket": "Where is my order #1042?"}, "It ships tomorrow."),
        weave_call("c2", "c1", "openai.chat.completions.create", 0.05, 1.3, {"model": "gpt-4o-mini"}, "Look up the order, then answer.",
                   usage={"gpt-4o-mini": {"prompt_tokens": 412, "completion_tokens": 18}}),
        weave_call("c3", "c1", "lookup_order", 1.35, 1.9, {"order_id": 1042, "attempt": 1}, exception=timeout),
        weave_call("c4", "c1", "lookup_order", 1.95, 2.6, {"order_id": 1042, "attempt": 2}, {"status": "packed", "ships": "tomorrow"}),
        weave_call("c5", "c1", "openai.chat.completions.create", 2.65, 4.05, {"model": "gpt-4o-mini"}, "It ships tomorrow.",
                   usage={"gpt-4o-mini": {"prompt_tokens": 503, "completion_tokens": 9}}),
    ]
    TraceView.from_weave(weave_calls, title="support_bot (offline)")
    return


if __name__ == "__main__":
    app.run()
