# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///

# MVP spike: prove we can *log* an async run inside a marimo notebook.
#
# No widget, no JS, no traitlets yet — just capture the event stream (spawn,
# suspend-at-await, resume, return, done) live on marimo's own event loop via
# top-level `await`, and show it as a table. If this looks right, it becomes the
# data model for the AsyncFlow timeline widget.

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="full")


@app.cell
def _():
    import asyncio
    import sys
    import time

    import marimo as mo

    return asyncio, mo, sys, time


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## AsyncFlow MVP — logging an async run

    Three standard hooks capture everything a timeline needs, live, on
    marimo's own loop:

    - `loop.set_task_factory(...)` → task **spawn** + who spawned whom
    - `task.add_done_callback(...)` → **done** + result / exception
    - `sys.monitoring` (PY_RESUME / PY_YIELD / PY_RETURN) → **suspend/resume**
      boundaries, each carrying the **source line**

    The example below runs `asyncio.gather` over three workers that sleep for
    different amounts. They *start* A, B, C but *finish* B, C, A — and the log
    proves the capture saw that real interleaving.
    """)
    return


@app.cell
def _(asyncio, sys, time):
    class AsyncFlowLogger:
        """Record the async event stream for a run, on the running loop.

        Usage (inside an async marimo cell)::

            async with AsyncFlowLogger(targets=[worker, main]) as log:
                result = await main()
            log.events  # list of {"t_ms", "coro", "event", "task", "line"}

        Only the coroutines in ``targets`` are logged (matched by code object),
        so asyncio's internals — and this logger's own methods, which share the
        notebook's source file — stay out of the stream.

        ``on_event(event)`` (if given) is called the instant each event is
        recorded — this is the live push hook the timeline widget will use to
        stream events into the browser. Keep it cheap: it runs inside the
        capture hooks.
        """

        _TOOL = sys.monitoring.PROFILER_ID

        def __init__(self, targets, on_event=None):
            self._codes = {fn.__code__ for fn in targets}
            self._on_event = on_event
            self.events = []
            self._t0 = None
            self._loop = None

        # -- helpers -------------------------------------------------------
        def _stamp(self):
            return round((time.perf_counter() - self._t0) * 1000, 2)

        def _current_task_name(self):
            # current_task() raises if called with no running loop (e.g. during
            # loop shutdown); treat that as the root.
            try:
                task = asyncio.current_task()
            except RuntimeError:
                return "root"
            return task.get_name() if task is not None else "root"

        @staticmethod
        def _line_of(code, offset):
            for start, end, lineno in code.co_lines():
                if lineno is not None and start <= offset < end:
                    return lineno
            return None

        def _record(self, coro_name, event, task, line=None, detail=None):
            entry = {
                "t_ms": self._stamp(),
                "coro": coro_name,
                "event": event,
                "task": task,
                "line": line,
                "detail": detail,
            }
            self.events.append(entry)
            if self._on_event is not None:
                self._on_event(entry)

        # -- task factory --------------------------------------------------
        def _task_factory(self, loop, coro, **kwargs):
            task = asyncio.Task(coro, loop=loop, **kwargs)
            # Only log tasks whose coroutine is one we're targeting.
            if getattr(coro, "cr_code", None) not in self._codes:
                return task
            name = getattr(coro, "__qualname__", str(coro))
            self._record(name, "SPAWN", task.get_name(), detail=f"by {self._current_task_name()}")

            def _on_done(t, coro_name=name):
                if t.cancelled():
                    detail = "cancelled"
                elif t.exception() is not None:
                    detail = f"raised {type(t.exception()).__name__}"
                else:
                    detail = repr(t.result())
                self._record(coro_name, "DONE", t.get_name(), detail=detail)

            task.add_done_callback(_on_done)
            return task

        # -- sys.monitoring callbacks -------------------------------------
        def _on_resume(self, code, offset):
            if code in self._codes:
                self._record(code.co_qualname, "RESUME", self._current_task_name())

        def _on_yield(self, code, offset, retval):
            if code in self._codes:
                self._record(
                    code.co_qualname, "SUSPEND", self._current_task_name(),
                    line=self._line_of(code, offset),
                )

        def _on_return(self, code, offset, retval):
            if code in self._codes:
                self._record(
                    code.co_qualname, "RETURN", self._current_task_name(),
                    line=self._line_of(code, offset),
                )

        # -- context manager ----------------------------------------------
        async def __aenter__(self):
            self._t0 = time.perf_counter()
            self._loop = asyncio.get_running_loop()
            self._loop.set_task_factory(self._task_factory)

            mon = sys.monitoring
            # A stale tool id (from a crashed prior run) would make use_tool_id
            # raise; free it defensively first.
            if mon.get_tool(self._TOOL) is not None:
                mon.free_tool_id(self._TOOL)
            mon.use_tool_id(self._TOOL, "asyncflow")
            events = mon.events
            mon.set_events(self._TOOL, events.PY_RESUME | events.PY_YIELD | events.PY_RETURN)
            mon.register_callback(self._TOOL, events.PY_RESUME, self._on_resume)
            mon.register_callback(self._TOOL, events.PY_YIELD, self._on_yield)
            mon.register_callback(self._TOOL, events.PY_RETURN, self._on_return)
            return self

        async def __aexit__(self, exc_type, exc, tb):
            mon = sys.monitoring
            mon.set_events(self._TOOL, 0)
            for event in (mon.events.PY_RESUME, mon.events.PY_YIELD, mon.events.PY_RETURN):
                mon.register_callback(self._TOOL, event, None)
            mon.free_tool_id(self._TOOL)
            if self._loop is not None:
                self._loop.set_task_factory(None)
            return False

    return (AsyncFlowLogger,)


@app.cell
def _(asyncio):
    # Defined in a cell (not @app.function) so worker/main share one source
    # filename the logger can target.
    async def worker(name, delay):
        await asyncio.sleep(delay)
        return name

    async def main():
        return await asyncio.gather(
            worker("A", 0.3),
            worker("B", 1.1),
            worker("C", 0.2),
            worker("D", 5.1),
        )

    return main, worker


@app.cell
def _(mo):
    def render(events, done):
        # A plain markdown table, rebuilt each tick — cheap enough for the demo.
        head = "| t_ms | coro | event | task | line | detail |\n|--:|--|--|--|--:|--|\n"
        rows = "\n".join(
            f"| {e['t_ms']} | `{e['coro']}` | **{e['event']}** | {e['task']} | "
            f"{'' if e['line'] is None else 'L' + str(e['line'])} | {e['detail'] or ''} |"
            for e in events
        )
        status = "✅ finished" if done else "🟢 running…"
        return mo.md(f"**{status}** — {len(events)} events captured\n\n{head}{rows}")

    return (render,)


@app.cell
async def _(AsyncFlowLogger, asyncio, main, mo, render, worker):
    log = AsyncFlowLogger(targets=[worker, main])
    async with log:
        run = asyncio.ensure_future(main())
        # LIVE: re-render the growing stream every 100ms while the run is still
        # in flight, so events appear as they fire (watch worker D linger ~5s).
        while not run.done():
            mo.output.replace(render(log.events, done=False))
            await asyncio.sleep(0.1)
        result = await run
    mo.output.replace(render(log.events, done=True))

    # CLI proof (visible under `uv run demos/asyncflow_mvp.py`).
    print(f"result: {result}")
    for e in log.events:
        line = "" if e["line"] is None else f"L{e['line']}"
        print(f"{e['t_ms']:>7} | {e['coro']:<8} | {e['event']:<8} | {e['task']:<8} | {line:<4} | {e['detail'] or ''}")
    done_order = [e["detail"] for e in log.events if e["event"] == "DONE" and e["coro"] == "worker"]
    print(f"worker completion order: {done_order}")
    return


if __name__ == "__main__":
    app.run()
