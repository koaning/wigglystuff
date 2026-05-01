# ThreeWidget API

::: wigglystuff.three_widget.ThreeWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict[str, Any]]` | Point list with `x`, `y`, `z`, and optional `color`/`size`. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `show_grid` | `bool` | Show the grid helper. |
| `show_axes` | `bool` | Show the axes helper. |
| `dark_mode` | `bool` | Toggle dark background and lighting. |
| `axis_labels` | `list[str]` | Optional labels for x/y/z axes. |
| `animate_updates` | `bool` | Animate transitions when updating points. |
| `animation_duration_ms` | `int` | Duration for animated updates in milliseconds. |
