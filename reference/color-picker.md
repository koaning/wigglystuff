# ColorPicker API


 Bases: `AnyWidget`


Simple color picker syncing a `#RRGGBB` hex value back to Python.



```
from wigglystuff import ColorPicker

picker = ColorPicker(color="#ff5733")
picker
```


Create a ColorPicker widget.


  Source code in `wigglystuff/color_picker.py`

```
def __init__(self, *, color: Optional[str] = None, **kwargs: Any):
    """Create a ColorPicker widget.

    Args:
        color: Optional starting hex color (e.g. ``"#ff00aa"``).
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if color is not None:
        kwargs["color"] = color
    super().__init__(**kwargs)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `color` | `str` | Hex color string (e.g., `#ff00aa`). |
