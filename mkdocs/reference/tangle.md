# Tangle Widgets API

## TangleSlider

::: wigglystuff.tangle.TangleSlider

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `amount` | `float` | Current value. |
| `min_value` | `float` | Lower bound. |
| `max_value` | `float` | Upper bound. |
| `step` | `float` | Step size. |
| `pixels_per_step` | `int` | Drag distance per step. |
| `prefix` | `str` | Text before the value. |
| `suffix` | `str` | Text after the value. |
| `digits` | `int` | Decimal precision for display. |


## TangleChoice

::: wigglystuff.tangle.TangleChoice

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `choice` | `str` | Current selection. |
| `choices` | `list[str]` | Available options. |


## TangleSelect

::: wigglystuff.tangle.TangleSelect

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `choice` | `str` | Current selection. |
| `choices` | `list[str]` | Available options. |

