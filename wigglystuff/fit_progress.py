"""Live progress view for scikit-learn fits, driven by sklearn's callback API."""

import os
import threading
import time
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import anywidget
import traitlets

from .html import _in_notebook


def _format_value(value: Any) -> str:
    """Short label for a hyperparameter value (3 significant digits for floats)."""
    if isinstance(value, float):
        return f"{value:.3g}"
    if hasattr(value, "get_params"):
        return type(value).__name__
    return str(value)


def _search_param_names(estimator: Any) -> list[str]:
    """Names of the hyperparameters a search estimator varies, in a stable order."""
    space = getattr(estimator, "param_grid", None)
    if space is None:
        space = getattr(estimator, "param_distributions", None)
    if space is None:
        return []
    names: list[str] = []
    for grid in space if isinstance(space, list) else [space]:
        for name in grid:
            if name not in names:
                names.append(name)
    return names


# A search's own per-fit tasks. They get a cell even when the inner estimator
# does not support callbacks (e.g. a random forest), in which case they are
# leaves with no progress of their own.
_SEARCH_FIT_TASKS = {"candidate-split-evaluation", "refit-with-best-params"}


def _propagation_depth(estimator: Any, requested: int | None) -> int | None:
    """The propagation depth to use for a fit of ``estimator``.

    ``0`` (propagate to no sub-estimator) when the sub-estimator reachable as
    ``estimator.estimator`` cannot receive callbacks, e.g. the random forest of
    a search: propagating to it would only make sklearn warn, once per fit,
    that it dropped the callback — and such an estimator reports no progress of
    its own below the outer estimator's tasks anyway, so nothing is lost.
    """
    inner = getattr(estimator, "estimator", None)
    if inner is not None and not hasattr(inner, "set_callbacks"):
        return 0
    return requested


@contextmanager
def _no_callback_support_warnings():
    """Mute sklearn's per-fit "does not support callbacks" warning.

    An estimator without callback support nested in one that has it (a random
    forest as a search's estimator or as a pipeline step) makes sklearn warn
    for every fit that it dropped the propagated callbacks. The widget draws
    those fits as striped bars regardless, so the warnings are noise here.
    Only this exact message is muted; every other warning still shows.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message=r"The estimator \w+ does not support callbacks\."
        )
        yield


class _FitProgressCallback:
    """The sklearn callback that ``FitProgress.fit`` attaches for the duration of a fit.

    It holds only a picklable handle to a listener in the notebook process, so
    it also works when the search runs its fits in worker processes (``n_jobs``).
    """

    def __init__(self, listener_handle: Any, param_names: list[str], max_propagation_depth: int | None) -> None:
        self.listener_handle = listener_handle
        self.param_names = param_names
        self.max_propagation_depth = max_propagation_depth

    def setup(self, estimator: Any, context: Any) -> None:
        pass

    def teardown(self, estimator: Any, context: Any) -> None:
        pass

    def on_fit_task_begin(self, estimator: Any, context: Any) -> None:
        # Leaf tasks (e.g. one lbfgs iteration) get no node of their own; their
        # end events are enough to advance the parent's bar.
        is_leaf = context.max_subtasks == 0 and context.parent is not None
        if is_leaf and context.source_task_name is None and context.task_name not in _SEARCH_FIT_TASKS:
            return
        message = {
            "event": "begin",
            "path": _path(context),
            "estimator": context.estimator_name,
            "task": context.task_name,
            "source_task": context.source_task_name,
            "total": context.max_subtasks,
        }
        if context.task_name == "search":
            message["n_splits"] = getattr(estimator, "n_splits_", None)
        if (context.source_task_name or context.task_name) == "candidate-split-evaluation":
            # The search scores this fit right after it, in the same worker;
            # that is how a test score finds its way back to this cell.
            message["worker"] = _worker()
        if context.source_task_name is not None:
            params = estimator.get_params(deep=True)
            message["params"] = _format_params(params, self.param_names)
            if isinstance(params.get("max_iter"), int):
                message["max_iter"] = params["max_iter"]
        self._send(message)

    def on_fit_task_end(self, estimator: Any, context: Any) -> None:
        # The task name tells the widget what a parent counts, e.g. "lbfgs-iter".
        self._send({"event": "end", "path": _path(context), "task": context.task_name})

    def _send(self, message: dict[str, Any]) -> None:
        from sklearn.callback._transport import send

        send(self.listener_handle, message)


class _ScoreReporter:
    """Wraps a search's scorer to report each test-fold score as it is computed.

    sklearn's callbacks don't see test scores: a search scores a fit after its
    last callback event. ``FitProgress.fit`` swaps this in as the search's
    ``scoring`` for the duration of the fit (and swaps the original back after).
    """

    def __init__(self, scorer: Any, listener_handle: Any) -> None:
        self.scorer = scorer
        self.listener_handle = listener_handle

    def __call__(self, estimator: Any, *args: Any, **kwargs: Any) -> Any:
        score = self.scorer(estimator, *args, **kwargs)
        from sklearn.callback._transport import send

        send(self.listener_handle, {"event": "score", "worker": _worker(), "score": float(score)})
        return score


def _worker() -> str:
    """Identifies the process and thread running a fit (fits run one at a time in each)."""
    return f"{os.getpid()}-{threading.get_ident()}"


def _path(context: Any) -> list[int]:
    path = []
    while context is not None:
        path.append(context.task_id)
        context = context.parent
    return path[::-1]


class FitProgress(anywidget.AnyWidget):
    """Live progress bars for a scikit-learn fit, with a grid view for hyperparameter searches.

    Display the widget, then run the fit through it. ``GridSearchCV`` and
    ``RandomizedSearchCV`` render as a candidates x folds grid: a running cell
    fills up with the inner estimator's progress (e.g. solver iterations), a
    finished cell shows its test score, and each row gets its mean score once
    all its folds are in. Other estimators render as nested bars.

    Outside a notebook, ``fit`` uses scikit-learn's own terminal ``ProgressBar``
    when ``rich`` is installed, and fits silently otherwise.

    Needs scikit-learn 1.9+ (``pip install wigglystuff[sklearn]``).

    Examples:
        ```python
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GridSearchCV
        from wigglystuff import FitProgress

        progress = FitProgress()
        progress  # show it in one cell ...

        # ... and fit through it in another
        grid = progress.fit(
            GridSearchCV(LogisticRegression(), {"C": [0.01, 0.1, 1.0]}, cv=5),
            X,
            y,
        )
        ```
    """

    _esm = Path(__file__).parent / "static" / "fit-progress.js"
    _css = Path(__file__).parent / "static" / "fit-progress.css"

    tasks = traitlets.List(traitlets.Dict()).tag(sync=True)
    candidates = traitlets.List(traitlets.Dict()).tag(sync=True)
    scores = traitlets.Dict(allow_none=True, default_value=None).tag(sync=True)
    color = traitlets.Unicode("").tag(sync=True)
    status = traitlets.Unicode("idle").tag(sync=True)
    started_ms = traitlets.Float(0.0).tag(sync=True)
    now_ms = traitlets.Float(0.0).tag(sync=True)
    sync_throttle_ms = traitlets.Int(100).tag(sync=True)

    def __init__(
        self,
        max_propagation_depth: int | None = None,
        color: str = "",
        sync_throttle_ms: int = 100,
        **kwargs: Any,
    ) -> None:
        """Create a FitProgress view.

        Args:
            max_propagation_depth: How many levels of nested estimators report
                progress. ``None`` (default) shows every level, e.g. the lbfgs
                iterations of a LogisticRegression inside a Pipeline inside a
                search; ``1`` stops at the search's direct inner estimator;
                ``0`` only shows the outer estimator.
            color: Optional CSS color for the bars, the score shading and the
                best row. Empty uses the default blue.
            sync_throttle_ms: Minimum milliseconds between updates sent to the
                browser while a fit is running.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if max_propagation_depth is not None and max_propagation_depth < 0:
            raise ValueError("max_propagation_depth must be >= 0 or None")
        if sync_throttle_ms < 0:
            raise ValueError("sync_throttle_ms must be >= 0")
        super().__init__(color=color, sync_throttle_ms=sync_throttle_ms, **kwargs)
        self.max_propagation_depth = max_propagation_depth
        self._lock = threading.Lock()
        self._nodes: dict[tuple[int, ...], dict[str, Any]] = {}
        self._cell_by_worker: dict[str, tuple[int, ...]] = {}
        self._last_sync = float("-inf")

    def fit(self, estimator: Any, X: Any, y: Any = None, **fit_params: Any) -> Any:
        """Fit ``estimator`` while this widget shows its progress; returns the fitted estimator.

        The progress callback is only attached for the duration of the fit, so
        the returned estimator keeps exactly the callbacks it had before.
        """
        if not hasattr(estimator, "set_callbacks"):
            raise TypeError(
                f"{type(estimator).__name__} does not support scikit-learn callbacks "
                "(needs scikit-learn 1.9+ and an estimator that implements them)"
            )
        if not _in_notebook():
            return self._fit_in_terminal(estimator, X, y, **fit_params)

        from sklearn.callback._transport import close_listener, open_listener

        self.clear()
        param_names = _search_param_names(estimator)
        self.candidates = _grid_candidates(estimator, param_names)
        self.status = "running"
        self.started_ms = time.time() * 1000
        handle = open_listener(self._on_message)
        depth = _propagation_depth(estimator, self.max_propagation_depth)
        callback = _FitProgressCallback(handle, param_names, depth)
        original = list(getattr(estimator, "_skl_callbacks", []))
        estimator.set_callbacks(*original, callback)
        # Single-metric searches report their fold scores live (multi-metric
        # ones only show scores once the search is done).
        scoring = getattr(estimator, "scoring", None)
        reporter = None
        if hasattr(estimator, "cv") and (scoring is None or isinstance(scoring, str) or callable(scoring)):
            from sklearn.metrics import check_scoring

            reporter = _ScoreReporter(check_scoring(estimator.estimator, scoring), handle)
            estimator.scoring = reporter
        try:
            with _no_callback_support_warnings():
                estimator.fit(X, y, **fit_params)
        except BaseException:
            self._finish("error")
            raise
        finally:
            estimator.set_callbacks(*original)
            if reporter is not None:
                estimator.scoring = scoring
                if getattr(estimator, "scorer_", None) is reporter:
                    estimator.scorer_ = reporter.scorer
            close_listener(handle)
        if hasattr(estimator, "cv_results_"):
            self.candidates = [_format_params(p, param_names) for p in estimator.cv_results_["params"]]
        self.scores = self._search_scores(estimator)
        self._finish("done")
        return estimator

    def clear(self) -> None:
        """Forget the previous run."""
        with self._lock:
            self._nodes = {}
            self._cell_by_worker = {}
        self.tasks = []
        self.candidates = []
        self.scores = None
        self.status = "idle"
        self.started_ms = 0.0
        self.now_ms = 0.0

    def _fit_in_terminal(self, estimator: Any, X: Any, y: Any, **fit_params: Any) -> Any:
        try:
            import rich  # noqa: F401
        except ImportError:
            return estimator.fit(X, y, **fit_params)
        from sklearn.callback import ProgressBar

        original = list(getattr(estimator, "_skl_callbacks", []))
        depth = _propagation_depth(estimator, self.max_propagation_depth)
        estimator.set_callbacks(*original, ProgressBar(max_propagation_depth=depth))
        try:
            with _no_callback_support_warnings():
                return estimator.fit(X, y, **fit_params)
        finally:
            estimator.set_callbacks(*original)

    def _on_message(self, message: dict[str, Any]) -> None:
        # Called from the fitting thread, or from listener threads when the
        # fits run in worker processes.
        now = time.time() * 1000
        event = message.pop("event")
        if event == "score":
            with self._lock:
                # The first score after a fit is its test score (a train score,
                # with return_train_score=True, comes second and is ignored).
                path = self._cell_by_worker.pop(message["worker"], None)
                if path in self._nodes:
                    self._nodes[path]["score"] = message["score"]
            self._sync()
            return
        path = tuple(message.pop("path"))
        with self._lock:
            if event == "begin":
                if "worker" in message:
                    self._cell_by_worker[message.pop("worker")] = path
                self._nodes[path] = {
                    **message,
                    "path": list(path),
                    "done": 0,
                    "state": "running",
                    "start_ms": now,
                    "end_ms": None,
                }
            else:
                node = self._nodes.get(path)
                if node is not None:
                    node["state"] = "done"
                    node["end_ms"] = now
                parent = self._nodes.get(path[:-1])
                if parent is not None:
                    parent["done"] += 1
                    if node is None:
                        parent["unit"] = message["task"]
        # Always show a task starting: an estimator without callback support
        # sends nothing else until it ends, so a throttled begin would leave
        # its cell blank for the whole fit.
        if event == "begin" or time.monotonic() - self._last_sync >= self.sync_throttle_ms / 1000:
            self._sync()

    def _sync(self) -> None:
        with self._lock:
            tasks = [dict(node) for _, node in sorted(self._nodes.items())]
        self._last_sync = time.monotonic()
        self.now_ms = time.time() * 1000
        self.tasks = tasks

    def _finish(self, status: str) -> None:
        with self._lock:
            for node in self._nodes.values():
                if node["state"] == "running":
                    node["state"] = "stopped"
        self._sync()
        self.status = status

    def _search_scores(self, estimator: Any) -> dict[str, Any] | None:
        """Per-fold test scores of a fitted search, laid out like the grid."""
        results = getattr(estimator, "cv_results_", None)
        n_splits = getattr(estimator, "n_splits_", None)
        if results is None or not n_splits:
            return None
        metric = "score"
        if isinstance(estimator.refit, str):
            metric = estimator.refit
        key = f"split{{}}_test_{metric}"
        if key.format(0) not in results:
            return None
        folds = [[_score(v) for v in results[key.format(k)]] for k in range(n_splits)]
        return {
            "metric": metric,
            "folds": [list(row) for row in zip(*folds)],
            "mean": [_score(v) for v in results[f"mean_test_{metric}"]],
            "rank": [int(v) for v in results[f"rank_test_{metric}"]],
            "best_index": int(getattr(estimator, "best_index_", -1)),
        }


def _format_params(params: dict[str, Any], param_names: list[str]) -> dict[str, str]:
    return {name: _format_value(params[name]) for name in param_names if name in params}


def _grid_candidates(estimator: Any, param_names: list[str]) -> list[dict[str, str]]:
    """A GridSearchCV's candidates, known before the fit (in the order it runs them)."""
    if getattr(estimator, "param_grid", None) is None:
        return []
    from sklearn.model_selection import ParameterGrid

    return [_format_params(p, param_names) for p in ParameterGrid(estimator.param_grid)]


def _score(value: Any) -> float | None:
    """A score as a JSON-safe float; failed fits (NaN) become ``None``."""
    value = float(value)
    return None if value != value else value
