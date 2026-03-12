# PlaySlider API

::: wigglystuff.play_slider.PlaySlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int` | Current slider value. |
| `min_value` | `int` | Minimum value. |
| `max_value` | `int` | Maximum value. |
| `step` | `int` | Step size per tick. |
| `interval_ms` | `int` | Milliseconds between auto-advance ticks. |
| `playing` | `bool` | Whether the slider is currently auto-advancing. |
| `loop` | `bool` | Whether to loop back to `min_value` after reaching `max_value`. |
| `width` | `int` | Widget width in pixels. |
