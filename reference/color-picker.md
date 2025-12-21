# ColorPicker API


 Bases: `AnyWidget`


Simple color picker syncing a `#RRGGBB` hex value back to Python.


Examples:


```
picker = ColorPicker(color="#ff5733")
picker
```


Create a ColorPicker widget.


Parameters:


| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `color` | `Optional[str]` | Optional starting hex color (e.g. `"#ff00aa"`). | `None` |
| `**kwargs` | `Any` | Forwarded to `anywidget.AnyWidget`. | `{}` |

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
