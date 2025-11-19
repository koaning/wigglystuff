from pathlib import Path

import anywidget
import traitlets


class KeystrokeWidget(anywidget.AnyWidget):
    """Capture the latest keyboard shortcut pressed inside the widget."""

    _esm = Path(__file__).parent / "static" / "keystroke-widget.js"
    last_key = traitlets.Dict(default_value={}).tag(sync=True)
