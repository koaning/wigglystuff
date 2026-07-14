# AsyncFlow API

::: wigglystuff.async_flow.AsyncFlow

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `events` | `list[dict]` | Captured event stream; re-synced on every poll tick so the timeline grows live. Each entry has `t_ms`, `coro`, `event`, `task`, `line`, `detail`. |
| `now_ms` | `float` | Elapsed wall-clock milliseconds; advances every tick so suspended bars keep growing during long sleeps. |
| `running` | `bool` | Whether a run is currently in flight. |
| `width` | `int` | Widget width in pixels; `0` grows to fit. |
