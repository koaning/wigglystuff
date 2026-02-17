# WandbChart API


 Bases: `AnyWidget`


Live line chart that polls wandb for metric data via the GraphQL API.


Renders a Canvas-based chart that auto-updates while runs are active. Supports multiple runs for side-by-side comparison and optional rolling smoothing (rolling mean, exponential moving average, or gaussian) with raw data shown behind the smoothed line.



```
from wigglystuff import WandbChart

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


Create a WandbChart widget.


  Source code in `wigglystuff/wandb_chart.py`

```
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
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `api_key` | `str` | Your wandb API key. |
| `entity` | `str` | The wandb entity (user or team). |
| `project` | `str` | The wandb project name. |
| `key` | `str` | The metric key to chart (e.g. `"loss"`). |
| `poll_seconds` | `int \\| None` | Seconds between polling updates, or `None` for manual refresh (default: 5). |
| `smoothing_kind` | `str` | Type of smoothing: `"rolling"`, `"exponential"`, or `"gaussian"` (default: `"gaussian"`). |
| `smoothing_param` | `float \\| None` | Smoothing parameter, or `None` for no smoothing. |
| `show_slider` | `bool` | Whether to show the smoothing slider (default: `True`). |
| `width` | `int` | Chart width in pixels (default: 700). |
| `height` | `int` | Chart height in pixels (default: 300). |
