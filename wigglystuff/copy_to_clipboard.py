from pathlib import Path
from typing import Any

import anywidget
import traitlets


class CopyToClipboard(anywidget.AnyWidget):
    """Button that copies provided text to the clipboard.

    Parameters
    ----------
    text_to_copy:
        Initial text payload placed behind the button. Defaults to an empty
        string.
    """

    text_to_copy = traitlets.Unicode("").tag(sync=True)
    _esm = Path(__file__).parent / "static" / "copybutton.js"
    _css = Path(__file__).parent / "static" / "copybutton.css"

    def __init__(self, text_to_copy: str = "", **kwargs: Any):
        """Create a CopyToClipboard button.

        Args:
            text_to_copy: Initial string placed on the clipboard when clicked.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(**kwargs)
        self.text_to_copy = text_to_copy
