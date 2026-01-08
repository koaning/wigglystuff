# ThreeWidget API


 Bases: `AnyWidget`


Interactive 3D scatter plot powered by Three.js.


The widget renders a collection of 3D points with per-point color and size attributes, suitable for quick exploratory visualizations in notebook environments.



```
from wigglystuff import ThreeWidget

data = [
    {"x": 1.0, "y": 2.0, "z": 3.0, "color": "tomato", "size": 0.2},
    {"x": -1.0, "y": 0.5, "z": -2.0, "color": "#22c55e", "size": 0.15},
]
widget = ThreeWidget(data=data, show_grid=True, show_axes=True)
widget
```


Create a ThreeWidget.


  Source code in `wigglystuff/three_widget.py`

```
def __init__(
    self,
    *,
    data: Optional[Iterable[dict[str, Any]]] = None,
    width: int = 600,
    height: int = 400,
    show_grid: bool = False,
    show_axes: bool = False,
    dark_mode: bool = False,
    axis_labels: Optional[Iterable[str]] = None,
    animate_updates: bool = False,
    animation_duration_ms: int = 400,
    auto_rotate: bool = False,
    auto_rotate_speed: float = 2.0,
    **kwargs: Any,
) -> None:
    """Create a ThreeWidget.

    Args:
        data: Iterable of dicts with ``x``, ``y``, ``z`` coordinates and
            optional ``color``/``size`` keys.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        show_grid: Whether to show a grid helper.
        show_axes: Whether to show axis helpers.
        dark_mode: Whether to render with a dark background.
        axis_labels: Optional axis labels for x/y/z.
        animate_updates: Whether to animate point updates.
        animation_duration_ms: Animation duration in milliseconds.
        auto_rotate: Whether to start with automatic rotation enabled.
        auto_rotate_speed: Speed of automatic rotation.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    super().__init__(
        data=list(data) if data is not None else [],
        width=width,
        height=height,
        show_grid=show_grid,
        show_axes=show_axes,
        dark_mode=dark_mode,
        axis_labels=list(axis_labels) if axis_labels is not None else [],
        animate_updates=animate_updates,
        animation_duration_ms=animation_duration_ms,
        auto_rotate=auto_rotate,
        auto_rotate_speed=auto_rotate_speed,
        **kwargs,
    )
```


## start_rotate


```
start_rotate(speed: float = 2.0) -> None
```


Start automatic rotation around the center of all points.


Rotation stops when the user interacts with the widget.


  Source code in `wigglystuff/three_widget.py`

```
def start_rotate(self, speed: float = 2.0) -> None:
    """Start automatic rotation around the center of all points.

    Rotation stops when the user interacts with the widget.

    Args:
        speed: Speed of automatic rotation.
    """
    self.auto_rotate_speed = speed
    self.auto_rotate = True
```


## update_points


```
update_points(
    updates: Iterable[Mapping[str, Any]],
    *,
    animate: bool = False,
    duration_ms: Optional[int] = None
) -> None
```


Update point properties in-place while preserving list length.


  Source code in `wigglystuff/three_widget.py`

```
def update_points(
    self,
    updates: Iterable[Mapping[str, Any]],
    *,
    animate: bool = False,
    duration_ms: Optional[int] = None,
) -> None:
    """Update point properties in-place while preserving list length.

    Args:
        updates: Iterable of dict-like updates aligned with existing points.
            Each update can include any subset of ``x``, ``y``, ``z``,
            ``color``, ``size`` keys.
        animate: Whether to animate the transition.
        duration_ms: Optional animation duration override in milliseconds.
    """
    update_list = list(updates)
    if len(update_list) != len(self.data):
        raise ValueError(
            "updates must have the same length as the current data list."
        )
    merged: list[dict[str, Any]] = []
    for current, update in zip(self.data, update_list):
        if not isinstance(update, Mapping):
            raise TypeError("Each update must be a mapping of point properties.")
        next_point = dict(current)
        next_point.update(update)
        merged.append(next_point)
    if duration_ms is not None:
        self.animation_duration_ms = duration_ms
    self.animate_updates = animate
    self.data = merged
```


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
