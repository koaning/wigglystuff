from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import anywidget
import traitlets


class AsyncFlowLogger:
    """Capture the event stream of an async run on the running event loop.

    Records task **spawn**, **suspend** (at an ``await``), **resume**, **return**,
    and **done** events into ``self.events`` — a list of dicts shaped like
    ``{"t_ms", "coro", "event", "task", "line", "detail"}``. Each event is also
    pushed to ``on_event`` the instant it is recorded (the live hook the widget
    uses to stream into the browser).

    Only coroutines whose source file is in ``files`` are logged, which keeps
    asyncio's own internals — and this module's code — out of the stream. The
    ``AsyncFlow`` widget seeds ``files`` from the traced coroutine's own file, so
    every coroutine defined alongside it (e.g. in the same notebook cell) is
    captured without the caller listing them.

    Requires ``sys.monitoring`` (Python 3.12+).
    """

    _TOOL = sys.monitoring.PROFILER_ID

    def __init__(
        self,
        files: Iterable[str],
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._files = set(files)
        # Code objects of coroutines we've seen spawned as tracked tasks. Only
        # these get fine-grained suspend/resume events — this excludes the
        # caller frame (e.g. the notebook cell awaiting us), which shares the
        # file but is not a task we drive.
        self._codes: set[Any] = set()
        self._on_event = on_event
        self.events: list[dict[str, Any]] = []
        self._t0: float | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    # -- helpers -----------------------------------------------------------
    def now_ms(self) -> float:
        return round((time.perf_counter() - self._t0) * 1000, 1)

    def _current_task_name(self) -> str:
        # current_task() raises with no running loop (e.g. at loop shutdown).
        try:
            task = asyncio.current_task()
        except RuntimeError:
            return "root"
        return task.get_name() if task is not None else "root"

    @staticmethod
    def _line_of(code: Any, offset: int) -> int | None:
        for start, end, lineno in code.co_lines():
            if lineno is not None and start <= offset < end:
                return lineno
        return None

    def _record(
        self, coro: str, event: str, task: str, line: int | None = None, detail: str | None = None
    ) -> None:
        entry = {
            "t_ms": self.now_ms(),
            "coro": coro,
            "event": event,
            "task": task,
            "line": line,
            "detail": detail,
        }
        self.events.append(entry)
        if self._on_event is not None:
            self._on_event(entry)

    # -- task factory ------------------------------------------------------
    def _task_factory(self, loop: Any, coro: Any, **kwargs: Any) -> asyncio.Task:
        task = asyncio.Task(coro, loop=loop, **kwargs)
        code = getattr(coro, "cr_code", None)
        if code is None or code.co_filename not in self._files:
            return task
        self._codes.add(code)
        name = getattr(coro, "__qualname__", str(coro))
        self._record(name, "SPAWN", task.get_name(), detail=f"by {self._current_task_name()}")

        def _on_done(t: asyncio.Task, coro_name: str = name) -> None:
            if t.cancelled():
                detail = "cancelled"
            elif t.exception() is not None:
                detail = f"raised {type(t.exception()).__name__}"
            else:
                detail = repr(t.result())
            self._record(coro_name, "DONE", t.get_name(), detail=detail)

        task.add_done_callback(_on_done)
        return task

    # -- sys.monitoring callbacks -----------------------------------------
    def _on_resume(self, code: Any, offset: int) -> None:
        if code in self._codes:
            self._record(code.co_qualname, "RESUME", self._current_task_name())

    def _on_yield(self, code: Any, offset: int, retval: Any) -> None:
        if code in self._codes:
            self._record(
                code.co_qualname, "SUSPEND", self._current_task_name(),
                line=self._line_of(code, offset),
            )

    def _on_return(self, code: Any, offset: int, retval: Any) -> None:
        if code in self._codes:
            self._record(
                code.co_qualname, "RETURN", self._current_task_name(),
                line=self._line_of(code, offset),
            )

    # -- context manager ---------------------------------------------------
    async def __aenter__(self) -> "AsyncFlowLogger":
        self._t0 = time.perf_counter()
        self._loop = asyncio.get_running_loop()
        self._loop.set_task_factory(self._task_factory)

        mon = sys.monitoring
        if mon.get_tool(self._TOOL) is not None:
            mon.free_tool_id(self._TOOL)
        mon.use_tool_id(self._TOOL, "asyncflow")
        ev = mon.events
        mon.set_events(self._TOOL, ev.PY_RESUME | ev.PY_YIELD | ev.PY_RETURN)
        mon.register_callback(self._TOOL, ev.PY_RESUME, self._on_resume)
        mon.register_callback(self._TOOL, ev.PY_YIELD, self._on_yield)
        mon.register_callback(self._TOOL, ev.PY_RETURN, self._on_return)
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        mon = sys.monitoring
        mon.set_events(self._TOOL, 0)
        for ev in (mon.events.PY_RESUME, mon.events.PY_YIELD, mon.events.PY_RETURN):
            mon.register_callback(self._TOOL, ev, None)
        mon.free_tool_id(self._TOOL)
        if self._loop is not None:
            self._loop.set_task_factory(None)
        return False


class AsyncFlow(anywidget.AnyWidget):
    """Live, source-linked timeline of a single async run.

    Runs a coroutine on the notebook's own event loop and streams its task
    activity — spawn, suspend-at-``await``, resume, done — into a swimlane
    timeline that fills in as the run proceeds. One lane per task; solid bars are
    running, hatched bars are suspended at an ``await``.

    Example (marimo, top-level ``await``)::

        import asyncio
        from wigglystuff import AsyncFlow

        async def worker(name, delay):
            await asyncio.sleep(delay)
            return name

        async def main():
            return await asyncio.gather(worker("A", 0.3), worker("B", 0.1))

        flow = await AsyncFlow.trace(main())   # displays live, returns the widget
        flow.result                            # ['A', 'B']

    Requires ``sys.monitoring`` (Python 3.12+).
    """

    _esm = Path(__file__).parent / "static" / "asyncflow.js"
    _css = Path(__file__).parent / "static" / "asyncflow.css"

    # The captured event stream, re-synced on every poll tick so the timeline
    # grows live. Each entry: {t_ms, coro, event, task, line, detail}.
    events = traitlets.List(default_value=[]).tag(sync=True)
    # Elapsed wall-clock ms; advances every tick so open (suspended) bars keep
    # growing even while no events fire (e.g. during a long sleep).
    now_ms = traitlets.Float(0.0).tag(sync=True)
    running = traitlets.Bool(False).tag(sync=True)
    # width: 0 means grow to fit; a positive value caps it.
    width = traitlets.Int(0).tag(sync=True)

    def __init__(self, *, width: int = 0, **kwargs: Any) -> None:
        super().__init__(width=width, **kwargs)
        self.result: Any = None

    async def run(
        self,
        coro: Any,
        *,
        targets: Iterable[Any] | None = None,
        poll_ms: int = 100,
    ) -> Any:
        """Drive ``coro`` to completion, streaming events into the widget.

        ``targets`` (functions/coroutines) add extra source files to capture;
        by default only the file of ``coro`` is tracked, which already picks up
        any coroutine defined alongside it.
        """
        files = set()
        code = getattr(coro, "cr_code", None)
        if code is not None:
            files.add(code.co_filename)
        for target in targets or []:
            target_code = getattr(target, "__code__", None) or getattr(target, "cr_code", None)
            if target_code is not None:
                files.add(target_code.co_filename)

        logger = AsyncFlowLogger(files, on_event=None)
        self.events = []
        self.now_ms = 0.0
        self.running = True
        try:
            async with logger:
                task = asyncio.ensure_future(coro)
                while not task.done():
                    self.now_ms = logger.now_ms()
                    self.events = list(logger.events)
                    await asyncio.sleep(poll_ms / 1000)
                self.result = await task
                self.now_ms = logger.now_ms()
                self.events = list(logger.events)
        finally:
            self.running = False
        return self.result

    @classmethod
    async def trace(
        cls,
        coro: Any,
        *,
        targets: Iterable[Any] | None = None,
        poll_ms: int = 100,
        width: int = 0,
    ) -> "AsyncFlow":
        """Create the widget, display it, and trace ``coro`` live.

        Returns the widget; the coroutine's return value is on ``.result``.
        """
        widget = cls(width=width)
        try:  # show it now so the timeline streams during the run
            import marimo as mo

            mo.output.append(widget)
        except Exception:  # noqa: BLE001 - display is best-effort (e.g. headless).
            pass
        await widget.run(coro, targets=targets, poll_ms=poll_ms)
        return widget
