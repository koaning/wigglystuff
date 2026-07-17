# CubeWidget API

::: wigglystuff.cube_widget.CubeWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `x_axis` | `dict` | X-axis display name and numeric values. |
| `y_axis` | `dict` | Y-axis display name and numeric values. |
| `z_axis` | `dict` | Z-axis display name and numeric values. |
| `locked_order` | `list[str]` | Axis keys in plane → line → point lock order. |
| `axis_values` | `dict[str, float]` | Current value for each axis key. |
| `plane` | `dict | None` | First locked axis display name and value. |
| `line` | `dict | None` | Second locked axis display name and value. |
| `point` | `dict | None` | Third locked axis display name and value. |

## Helpers

- `lock_axis(axis_key, value=None)` locks an axis and optionally sets its value.
- `unlock_axis(axis_key)` removes an axis from the lock order.
- `reset()` clears every lock while preserving the current axis values.
