"""StateViewer widget — animate the state inside one run of a Python function."""

from __future__ import annotations

import ast
import copy
import html
import inspect
import math
import sys
import textwrap
from pathlib import Path
from typing import Any, Callable

import anywidget
import traitlets

from .live_edit import _AnnotationBuilder, _render_html

_MAX_REPR = 120


class _StepLimit(BaseException):
    """Raised from the tracer to abort the run once ``max_steps`` is reached.

    A ``BaseException`` so a broad ``except Exception`` inside the traced
    function can't swallow it.
    """


def _short_repr(value: Any) -> str:
    try:
        text = repr(value)
    except Exception:  # noqa: BLE001 - a broken __repr__ shouldn't kill the trace.
        text = f"<{type(value).__name__}>"
    if len(text) > _MAX_REPR:
        text = text[: _MAX_REPR - 1] + "…"
    return text


def _snapshot(value: Any) -> Any:
    """Copy a local so later in-place mutations don't rewrite earlier steps."""
    try:
        return copy.deepcopy(value)
    except Exception:  # noqa: BLE001 - uncopyable objects are kept by reference.
        return value


def _view_to_html(value: Any) -> str:
    """Render a view_func result the way marimo would show it in a cell.

    Plain strings are treated as raw HTML/SVG. Anything else goes through
    ``marimo.as_html`` when marimo is installed, then the duck-typed
    ``_display_``/``_mime_``/``_repr_html_`` protocols, then an escaped repr.
    """
    if isinstance(value, str):
        return value
    try:
        import marimo

        return marimo.as_html(value).text
    except Exception:  # noqa: BLE001 - marimo missing or can't format this value.
        pass
    rich = _render_html(value)
    if rich is not None:
        return rich
    return f"<pre>{html.escape(_short_repr(value))}</pre>"


def _source_lines(fn: Callable[..., Any]) -> tuple[str, list[dict[str, Any]], int]:
    """Return the function's source (decorators dropped), its syntax-token
    lines, and how many decorator lines were dropped from the top."""
    if not inspect.isfunction(fn):
        raise TypeError(
            f"StateViewer expected a plain Python function, got {type(fn).__name__}."
        )
    try:
        code = textwrap.dedent(inspect.getsource(fn))
    except (OSError, TypeError) as exc:
        raise TypeError(
            "StateViewer could not find the source of this function. "
            "Plain top-level `def` functions work best."
        ) from exc
    # Drop decorator lines (e.g. marimo's `@app.function`) so the panel starts
    # at `def`. co_firstlineno points at the first decorator, so the recorder
    # subtracts `skipped` to keep step line numbers aligned with this source.
    skipped = ast.parse(code).body[0].lineno - 1
    code = "\n".join(code.splitlines()[skipped:]) + "\n"
    lines = _AnnotationBuilder(code, fn.__name__).build(ast.parse(code))["lines"]
    return code, [{"text": line["text"], "tokens": line["tokens"]} for line in lines], skipped


def _bind(params, local_values: dict[str, Any]) -> dict[str, Any] | None:
    """Keyword arguments for a callback whose parameter names pick the locals.

    A missing local falls back to the parameter's default; returns ``None``
    when a required one isn't assigned yet.
    """
    kwargs = {}
    for param in params:
        if param.kind is param.VAR_KEYWORD:
            kwargs.update(local_values)
        elif param.name in local_values:
            kwargs[param.name] = local_values[param.name]
        elif param.default is param.empty and param.kind is not param.VAR_POSITIONAL:
            return None
    return kwargs


class _Recorder:
    """sys.settrace hook that records one step per executed line of ``fn``."""

    def __init__(
        self, fn, view_func, max_steps, skipped_lines=0, shown=None, timeline_func=None
    ):
        self.code = fn.__code__
        self.first_line = fn.__code__.co_firstlineno + skipped_lines
        self.names = set(self.code.co_varnames) | set(self.code.co_cellvars)
        # Locals whose repr goes into the step record (the variables table).
        self.shown = set(shown) if shown is not None else self.names
        self.view_func = view_func
        self.view_params = (
            list(inspect.signature(view_func).parameters.values()) if view_func else []
        )
        self.timeline_func = timeline_func
        self.timeline_params = (
            list(inspect.signature(timeline_func).parameters.values())
            if timeline_func
            else []
        )
        self.max_steps = max_steps
        self.steps: list[dict[str, Any]] = []
        # Snapshots of the real local values, one per step. Python-side only.
        self.states: list[dict[str, Any]] = []
        self.views: list[str] = []
        self.view_index: dict[str, int] = {}
        self.depth = 0
        self.raising = False
        self.truncated = False
        # First exception raised by view_func/timeline_func, and which one.
        self.callback_error: BaseException | None = None
        self.callback_source = ""

    def global_trace(self, frame, event, arg):
        if event == "call" and frame.f_code is self.code:
            self.depth += 1
            return self.local_trace
        return None

    def local_trace(self, frame, event, arg):
        if event == "line":
            self.raising = False
            self.record(frame, "line")
        elif event == "exception":
            self.raising = True
        elif event == "return":
            # A frame unwinding because of an exception also fires "return"
            # (with arg None); label it as a raise instead.
            if self.raising:
                self.record(frame, "raise")
            else:
                self.record(frame, "return", returned=arg)
            self.depth -= 1
        return self.local_trace

    def record(self, frame, event, returned=None):
        if self.truncated or self.callback_error is not None:
            return
        if len(self.steps) >= self.max_steps:
            self.truncated = True
            raise _StepLimit
        local_values = {
            name: value for name, value in frame.f_locals.items() if name in self.names
        }
        step = {
            "line": frame.f_lineno - self.first_line + 1,
            "depth": self.depth,
            "event": event,
            "view": self.render_view(local_values) if self.view_func else -1,
            "locals": {
                name: _short_repr(value)
                for name, value in local_values.items()
                if name in self.shown
            },
        }
        if self.timeline_func:
            step["value"] = self.timeline_value(local_values)
        if event == "return":
            step["returned"] = _short_repr(returned)
        self.steps.append(step)
        self.states.append({name: _snapshot(value) for name, value in local_values.items()})

    def render_view(self, local_values: dict[str, Any]) -> int:
        """Call view_func on the matching locals; return an index into ``views``.

        If a required parameter isn't assigned yet, the previous step's view is
        reused (or -1 when there is none, which the frontend shows as an empty
        panel).
        """
        kwargs = _bind(self.view_params, local_values)
        if kwargs is None:
            return self.steps[-1]["view"] if self.steps else -1
        try:
            rendered = _view_to_html(self.view_func(**kwargs))
        except Exception as exc:  # noqa: BLE001 - surfaced through `error`.
            self.fail("view_func", exc)
        if rendered not in self.view_index:
            self.view_index[rendered] = len(self.views)
            self.views.append(rendered)
        return self.view_index[rendered]

    def timeline_value(self, local_values: dict[str, Any]) -> float:
        """Call timeline_func on the matching locals; the number to plot.

        While a required parameter isn't assigned yet, the previous step's
        value is reused (0 before the first one).
        """
        kwargs = _bind(self.timeline_params, local_values)
        if kwargs is None:
            return self.steps[-1]["value"] if self.steps else 0.0
        try:
            value = float(self.timeline_func(**kwargs))
            if not math.isfinite(value):
                raise ValueError(f"timeline_func returned {value}; it must be finite.")
        except Exception as exc:  # noqa: BLE001 - surfaced through `error`.
            self.fail("timeline_func", exc)
        return value

    def fail(self, source: str, exc: BaseException) -> None:
        """Remember a callback's exception and stop the run."""
        self.callback_error = exc
        self.callback_source = source
        raise _StepLimit from exc


class StateViewer(anywidget.AnyWidget):
    """Animate the state inside one run of a Python function.

    ``search_func`` is run once under ``sys.settrace``. Every executed line of
    it (recursive calls included, helpers stay opaque) becomes one step. At
    each step ``view_func`` is called with the function's locals matched to
    its parameters by name, so ``def view(board, n): ...`` receives the live
    ``board`` and ``n``. Parameters with a default are optional; while a
    required one isn't assigned yet the previous view stays up.

    ``view_func`` can return anything marimo can show: an HTML/SVG string,
    ``mo.Html``/``mo.md``, a dataframe, even a matplotlib figure. Views are
    rendered eagerly (so in-place mutations are captured correctly) and
    deduplicated. SVG strings are by far the fastest choice for long runs.

    ``view_func`` is optional. The widget's real job is to publish the state:
    ``step`` syncs to Python while playing and scrubbing (at most every
    ``sync_throttle_ms``), ``current`` holds the step's line, depth and value
    reprs, and ``state`` holds the actual local values at that step. Any other
    widget can draw it, e.g. ``viewer.observe(redraw, names="step")`` or a
    marimo cell that reads ``viewer.state`` and updates another widget.

    Examples:
        ```python
        from wigglystuff import StateViewer

        def solve(board, row, n):
            if row == n:
                return True
            for col in range(n):
                if all(c != col and abs(c - col) != row - r for r, c in enumerate(board)):
                    board.append(col)
                    if solve(board, row + 1, n):
                        return True
                    board.pop()
            return False

        def view(board, n):
            return "<pre>" + "\\n".join("." * c + "Q" + "." * (n - c - 1) for c in board) + "</pre>"

        StateViewer(solve, view, args=([], 0, 6))
        ```

        Without a view, drive another widget from the current state:

        ```python
        viewer = StateViewer(solve, args=([], 0, 6), variables=["board", "row"])
        viewer.observe(lambda _: print(viewer.state["board"]), names="step")
        ```
    """

    _esm = Path(__file__).parent / "static" / "state-viewer.js"
    _css = Path(__file__).parent / "static" / "state-viewer.css"

    code = traitlets.Unicode("").tag(sync=True)
    lines = traitlets.List(traitlets.Dict()).tag(sync=True)
    steps = traitlets.List(traitlets.Dict()).tag(sync=True)
    views = traitlets.List(traitlets.Unicode()).tag(sync=True)
    # The variables table rows: every local the run ever assigned in definition
    # order (or the names passed as `variables=`), so the table keeps a fixed
    # set of rows instead of growing as names appear.
    variables = traitlets.List(traitlets.Unicode()).tag(sync=True)
    step = traitlets.Int(0).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
    interval_ms = traitlets.Int(80).tag(sync=True)
    loop = traitlets.Bool(False).tag(sync=True)
    returned = traitlets.Unicode(default_value=None, allow_none=True).tag(sync=True)
    error = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    truncated = traitlets.Bool(False).tag(sync=True)
    # 0 = grow to fit content; a positive value caps the height and scrolls.
    height = traitlets.Int(0).tag(sync=True)
    # What the timeline plots: call depth, or the name of `timeline_func`.
    timeline_label = traitlets.Unicode("call depth").tag(sync=True)
    # Cap on how often `step` reaches Python while playing or scrubbing.
    sync_throttle_ms = traitlets.Int(100).tag(sync=True)

    def __init__(
        self,
        search_func: Callable[..., Any],
        view_func: Callable[..., Any] | None = None,
        *,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        max_steps: int = 20_000,
        only_changes: bool = False,
        interval_ms: int = 80,
        loop: bool = False,
        height: int = 0,
        variables: list[str] | None = None,
        sync_throttle_ms: int = 100,
        timeline_func: Callable[..., Any] | None = None,
        timeline_label: str | None = None,
        **widget_kwargs: Any,
    ) -> None:
        """Create a StateViewer.

        Args:
            search_func: The function to trace. Needs inspectable Python source.
            view_func: Draws the state; its parameter names pick the locals it gets.
                Optional: leave it out to only show code, variables and timeline.
            args: Positional arguments for ``search_func``.
            kwargs: Keyword arguments for ``search_func``.
            max_steps: Stop tracing after this many steps (sets ``truncated``).
            only_changes: Drop steps whose view (or, without a view, whose shown
                values) is identical to the previous step's.
            interval_ms: Milliseconds per step while playing.
            loop: Restart from the first step when playback reaches the end.
            height: Height cap in pixels (0 = fit content).
            variables: Local names to show in the variables table, in this order.
                Defaults to every local. ``state`` always holds all of them.
            sync_throttle_ms: Cap on how often ``step`` syncs to Python while
                playing or scrubbing, in milliseconds (0 = every step).
            timeline_func: Returns the number the timeline plots at each step;
                its parameter names pick the locals, like ``view_func``.
                Defaults to the call depth of ``search_func``, which stays flat
                for a search without recursion, so pass e.g.
                ``lambda queue: len(queue)`` there.
            timeline_label: Name shown for the timeline value. Defaults to
                ``timeline_func``'s name, or "value" for a lambda.
            **widget_kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if max_steps <= 0:
            raise ValueError("max_steps must be positive.")
        if interval_ms <= 0:
            raise ValueError("interval_ms must be positive.")
        if view_func is not None and not callable(view_func):
            raise TypeError("view_func must be callable.")
        if timeline_func is not None and not callable(timeline_func):
            raise TypeError("timeline_func must be callable.")
        if timeline_label is None:
            name = getattr(timeline_func, "__name__", "<lambda>")
            if timeline_func is None:
                timeline_label = "call depth"
            else:
                timeline_label = "value" if name == "<lambda>" else name
        code, lines, skipped = _source_lines(search_func)
        fn_code = search_func.__code__
        # dict.fromkeys dedupes: a local captured by a closure or generator
        # expression is listed in both co_varnames and co_cellvars.
        all_names = list(dict.fromkeys((*fn_code.co_varnames, *fn_code.co_cellvars)))
        if variables is not None:
            unknown = [name for name in variables if name not in all_names]
            if unknown:
                raise ValueError(
                    f"Unknown variables {unknown}; {search_func.__name__} has {all_names}."
                )
        recorder = _Recorder(
            search_func, view_func, max_steps, skipped, variables, timeline_func
        )
        returned = None
        error = None
        previous_trace = sys.gettrace()
        sys.settrace(recorder.global_trace)
        try:
            returned = _short_repr(search_func(*args, **(kwargs or {})))
        except _StepLimit:
            pass
        except Exception as exc:  # noqa: BLE001 - search errors are data, not crashes.
            error = self._error_payload(exc, recorder, "search_func")
        finally:
            sys.settrace(previous_trace)
        if recorder.callback_error is not None:
            error = self._error_payload(
                recorder.callback_error, recorder, recorder.callback_source
            )

        steps = recorder.steps
        states = recorder.states
        if only_changes:
            key = "view" if view_func is not None else "locals"
            keep = [i for i in range(len(steps)) if i == 0 or steps[i][key] != steps[i - 1][key]]
            steps = [steps[i] for i in keep]
            states = [states[i] for i in keep]
        self._states = states
        if variables is None:
            seen = {name for s in steps for name in s["locals"]}
            variables = [name for name in all_names if name in seen]
        super().__init__(
            code=code,
            lines=lines,
            steps=steps,
            views=recorder.views,
            variables=variables,
            interval_ms=interval_ms,
            loop=loop,
            returned=returned,
            error=error,
            truncated=recorder.truncated,
            height=height,
            sync_throttle_ms=sync_throttle_ms,
            timeline_label=timeline_label,
            **widget_kwargs,
        )

    @staticmethod
    def _error_payload(exc, recorder, source):
        payload = {"type": type(exc).__name__, "message": str(exc), "source": source}
        if recorder.steps:
            payload["lineno"] = recorder.steps[-1]["line"]
        return payload

    @property
    def n_steps(self) -> int:
        """Number of recorded steps."""
        return len(self.steps)

    @property
    def current(self) -> dict[str, Any] | None:
        """The step record at ``step`` (line, depth, event, view, locals)."""
        if not self.steps:
            return None
        return self.steps[max(0, min(self.step, len(self.steps) - 1))]

    @property
    def state(self) -> dict[str, Any] | None:
        """The actual local values at ``step``, copied when the step was recorded."""
        if not self._states:
            return None
        return self._states[max(0, min(self.step, len(self._states) - 1))]
