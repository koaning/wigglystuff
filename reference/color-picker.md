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
def __init__(
    self,
    *,
    color: Optional[str] = None,
    show_label: bool = True,
    **kwargs: Any,
):
    """Create a ColorPicker widget.

    Args:
        color: Optional starting hex color (e.g. ``"#ff00aa"``).
        show_label: Whether to show the hex label next to the picker.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if color is None:
        color = "#000000"
    super().__init__(color=color, show_label=show_label, **kwargs)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `color` | `str` | Hex color string (e.g., `#ff00aa`). |
