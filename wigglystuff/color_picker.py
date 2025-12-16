from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


class ColorPicker(anywidget.AnyWidget):
    """Simple color picker syncing a ``#RRGGBB`` hex value back to Python.

    Examples:
        ```python
        picker = ColorPicker(color="#ff5733")
        picker
        ```
    """

    _esm = Path(__file__).parent / "static" / "colorpicker.js"
    color = traitlets.Unicode("#000000").tag(sync=True)

    def __init__(self, *, color: Optional[str] = None, **kwargs: Any):
        """Create a ColorPicker widget.

        Args:
            color: Optional starting hex color (e.g. ``"#ff00aa"``).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if color is not None:
            kwargs["color"] = color
        super().__init__(**kwargs)

    @property
    def rgb(self):
        return tuple(int(self.color[i : i + 2], 16) for i in (1, 3, 5))
