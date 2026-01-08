# Slider2D API


 Bases: `AnyWidget`


Two dimensional slider for simultaneous adjustments.


Emits synchronized `x`/`y` floats that stay within configurable bounds while rendering to a pixel canvas sized via `width`/`height`.



```
from wigglystuff import Slider2D

slider = Slider2D(x=0.5, y=0.5, x_bounds=(0.0, 1.0), y_bounds=(0.0, 1.0))
slider
```


Create a Slider2D widget.


  Source code in `wigglystuff/slider2d.py`

```
def __init__(
    self,
    x: float = 0.0,
    y: float = 0.0,
    width: int = 400,
    height: int = 400,
    x_bounds: tuple[float, float] = (-1.0, 1.0),
    y_bounds: tuple[float, float] = (-1.0, 1.0),
    **kwargs: Any,
) -> None:
    """Create a Slider2D widget.

    Args:
        x: Initial x coordinate.
        y: Initial y coordinate.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        x_bounds: Min/max tuple for x.
        y_bounds: Min/max tuple for y.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    super().__init__(
        x=x,
        y=y,
        width=width,
        height=height,
        x_bounds=x_bounds,
        y_bounds=y_bounds,
        **kwargs,
    )
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `x` | `float` | Current x position. |
| `y` | `float` | Current y position. |
| `x_bounds` | `tuple[float, float]` | Min/max x bounds. |
| `y_bounds` | `tuple[float, float]` | Min/max y bounds. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
