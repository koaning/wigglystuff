from pathlib import Path

import anywidget
import traitlets


class KeystrokeWidget(anywidget.AnyWidget):
    """Capture the latest keyboard shortcut pressed inside the widget.

    No initialization arguments are required; the widget simply records
    keystrokes into the ``last_key`` trait.

    The ``last_key`` payload mirrors browser ``KeyboardEvent`` data with:
    ``key``, ``code``, modifier booleans (``ctrlKey``, ``shiftKey``,
    ``altKey``, ``metaKey``), and a ``timestamp`` in milliseconds since epoch.

    Examples:
        ```python
        keystroke = KeystrokeWidget()
        keystroke
        ```
    """

    _esm = Path(__file__).parent / "static" / "keystroke-widget.js"
    _css = Path(__file__).parent / "static" / "keystroke.css"
    last_key = traitlets.Dict(default_value={}).tag(sync=True)
