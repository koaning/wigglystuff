from pathlib import Path

import anywidget
import traitlets


class CopyToClipboard(anywidget.AnyWidget):
    """Button that copies provided text to the clipboard."""

    text_to_copy = traitlets.Unicode("").tag(sync=True)
    _esm = Path(__file__).parent / "static" / "copybutton.js"
    _css = Path(__file__).parent / "static" / "copybutton.css"

    def __init__(self, text_to_copy: str = "", **kwargs):
        super().__init__(**kwargs)
        self.text_to_copy = text_to_copy
