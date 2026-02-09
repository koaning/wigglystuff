"""WandbChart widget for live wandb run visualization."""

from pathlib import Path
from typing import Any, Optional, Sequence

import anywidget
import traitlets


class WandbChart(anywidget.AnyWidget):
    """Live line chart that polls wandb for metric data via the GraphQL API.

    Renders a Canvas-based chart that auto-updates while runs are active.
    Supports multiple runs for side-by-side comparison and optional rolling
    mean smoothing with raw data shown behind the smoothed line.

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
    rolling_mean = traitlets.Int(None, allow_none=True).tag(sync=True)
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
            rolling_mean: Rolling mean window size, or ``None`` for no smoothing.
                Must be ``>= 2`` when set.
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

    @traitlets.validate("rolling_mean")
    def _validate_rolling_mean(self, proposal: dict[str, Any]) -> Optional[int]:
        """Ensure rolling_mean is None or >= 2."""
        value = proposal["value"]
        if value is None:
            return value
        if value < 2:
            raise ValueError("rolling_mean must be None (no smoothing) or >= 2")
        return value
