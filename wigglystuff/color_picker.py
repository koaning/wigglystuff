from pathlib import Path

import anywidget
import traitlets


class ColorPicker(anywidget.AnyWidget):
    """Simple color picker that exposes RGB values."""

    _esm = Path(__file__).parent / "static" / "colorpicker.js"
    color = traitlets.Unicode("#000000").tag(sync=True)

    def __init__(self, *, color: str | None = None, **kwargs):
        if color is not None:
            kwargs["color"] = color
        super().__init__(**kwargs)

    @property
    def rgb(self):
        return tuple(int(self.color[i : i + 2], 16) for i in (1, 3, 5))
