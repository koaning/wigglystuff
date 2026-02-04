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
    _css = Path(__file__).parent / "static" / "colorpicker.css"
    color = traitlets.Unicode("#000000").tag(sync=True)
    show_label = traitlets.Bool(True).tag(sync=True)

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

    @property
    def rgb(self):
        return tuple(int(self.color[i : i + 2], 16) for i in (1, 3, 5))
