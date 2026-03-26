# PlaySlider API


 Bases: `AnyWidget`


Slider with a play/pause button that auto-advances at a configurable pace.



```
from wigglystuff import PlaySlider

from wigglystuff import PlaySlider

slider = PlaySlider(min_value=0, max_value=50, step=1, interval_ms=300)
slider
```


Create a PlaySlider.


  Source code in `wigglystuff/play_slider.py`

```
def __init__(
    self,
    value: Optional[float] = None,
    min_value: float = 0.0,
    max_value: float = 100.0,
    step: float = 1.0,
    interval_ms: int = 200,
    loop: bool = False,
    width: int = 400,
    **kwargs: Any,
) -> None:
    """Create a PlaySlider.

    Args:
        value: Starting position; defaults to *min_value*.
        min_value: Lower bound.
        max_value: Upper bound.
        step: Increment per tick.
        interval_ms: Milliseconds between auto-advance ticks.
        loop: Wrap to *min_value* when reaching the end instead of stopping.
        width: Widget width in pixels.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if min_value >= max_value:
        raise ValueError("min_value must be less than max_value.")
    if step <= 0:
        raise ValueError("step must be positive.")
    if value is None:
        value = min_value
    super().__init__(
        value=value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        interval_ms=interval_ms,
        loop=loop,
        width=width,
        **kwargs,
    )
```


## values `property`


```
values
```


All discrete values from min_value to max_value (inclusive) at the current step.


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
