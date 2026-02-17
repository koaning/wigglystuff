# WandbChart API

::: wigglystuff.wandb_chart.WandbChart

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `api_key` | `str` | Your wandb API key. |
| `entity` | `str` | The wandb entity (user or team). |
| `project` | `str` | The wandb project name. |
| `key` | `str` | The metric key to chart (e.g. `"loss"`). |
| `poll_seconds` | `int \| None` | Seconds between polling updates, or `None` for manual refresh (default: 5). |
| `smoothing_kind` | `str` | Type of smoothing: `"rolling"`, `"exponential"`, or `"gaussian"` (default: `"gaussian"`). |
| `smoothing_param` | `float \| None` | Smoothing parameter, or `None` for no smoothing. |
| `show_slider` | `bool` | Whether to show the smoothing slider (default: `True`). |
| `width` | `int` | Chart width in pixels (default: 700). |
| `height` | `int` | Chart height in pixels (default: 300). |
