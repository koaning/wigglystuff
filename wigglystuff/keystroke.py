from pathlib import Path

import anywidget
import traitlets


class KeystrokeWidget(anywidget.AnyWidget):
    """Capture the latest keyboard shortcut pressed inside the widget.

    No initialization arguments are required; the widget simply records
    keystrokes into the ``last_key`` trait.
    """

    _esm = Path(__file__).parent / "static" / "keystroke-widget.js"
    last_key = traitlets.Dict(default_value={}).tag(sync=True)
