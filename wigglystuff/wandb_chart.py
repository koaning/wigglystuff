"""WandbChart widget for live wandb run visualization."""

from pathlib import Path
from typing import Any, Optional, Sequence

import anywidget
import traitlets


class WandbChart(anywidget.AnyWidget):
    """Live line chart that polls wandb for metric data via the GraphQL API.

    Renders a Canvas-based chart that auto-updates while runs are active.
    Supports multiple runs for side-by-side comparison and optional rolling
    smoothing (rolling mean, exponential moving average, or gaussian)
    with raw data shown behind the smoothed line.

    Examples:
        ```python
        import wandb
        from wigglystuff import WandbChart, EnvConfig

        config = EnvConfig(["WANDB_API_KEY"])
        config.require_valid()

        run = wandb.init(project="my-project")
        chart = WandbChart(
            api_key=config["WANDB_API_KEY"],
            entity=run.entity,
            project=run.project,
            runs=[run],
            key="loss",
        )
        chart
        ```
    """

    _esm = Path(__file__).parent / "static" / "wandb-chart.js"

    api_key = traitlets.Unicode().tag(sync=True)
    entity = traitlets.Unicode().tag(sync=True)
    project = traitlets.Unicode().tag(sync=True)
    _runs = traitlets.List(traitlets.Dict()).tag(sync=True)
    key = traitlets.Unicode().tag(sync=True)
    poll_seconds = traitlets.Int(5, allow_none=True).tag(sync=True)
    smoothing_kind = traitlets.Unicode("gaussian").tag(sync=True)
    smoothing_param = traitlets.Float(None, allow_none=True).tag(sync=True)
    show_slider = traitlets.Bool(True).tag(sync=True)
    width = traitlets.Int(700).tag(sync=True)
    height = traitlets.Int(300).tag(sync=True)

    def __init__(
        self,
        *args: Any,
        runs: Optional[Sequence[Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Create a WandbChart widget.

        Args:
            api_key: Your wandb API key.
            entity: The wandb entity (user or team).
            project: The wandb project name.
            runs: A list of wandb Run objects or dicts with ``id`` and ``label`` keys.
            key: The metric key to chart (e.g. ``"loss"``).
            poll_seconds: Seconds between polling updates, or ``None`` to
                disable auto-polling and show a manual refresh button instead.
            smoothing_kind: Type of smoothing: ``"rolling"``, ``"exponential"``,
                or ``"gaussian"``. Defaults to ``"rolling"``.
            smoothing_param: Smoothing parameter, or ``None`` for no smoothing.
                For ``"rolling"``: integer window size ``>= 2``.
                For ``"exponential"``: EMA weight on previous value, ``0 < alpha < 1``.
                For ``"gaussian"``: standard deviation (sigma) ``> 0``.
            show_slider: Whether to show the smoothing slider in the UI.
            width: Chart width in pixels.
            height: Chart height in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if runs is not None:
            kwargs["_runs"] = [
                {"id": r.id, "label": r.name} if hasattr(r, "id") else r
                for r in runs
            ]
        super().__init__(*args, **kwargs)

    @traitlets.validate("smoothing_kind")
    def _validate_smoothing_kind(self, proposal: dict[str, Any]) -> str:
        value = proposal["value"]
        allowed = ("rolling", "exponential", "gaussian")
        if value not in allowed:
            raise ValueError(f"smoothing_kind must be one of {allowed}, got {value!r}")
        return value

    @traitlets.validate("smoothing_param")
    def _validate_smoothing_param(self, proposal: dict[str, Any]) -> Optional[float]:
        value = proposal["value"]
        if value is None:
            return value
        kind = self.smoothing_kind
        if kind == "rolling" and (value < 2 or value != int(value)):
            raise ValueError("For rolling smoothing, param must be an integer >= 2")
        if kind == "exponential" and not (0 < value < 1):
            raise ValueError("For exponential smoothing, param must be between 0 and 1 (exclusive)")
        if kind == "gaussian" and value <= 0:
            raise ValueError("For gaussian smoothing, param (sigma) must be > 0")
        return value
