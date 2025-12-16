from pathlib import Path

import anywidget
import traitlets


class WebkitSpeechToTextWidget(anywidget.AnyWidget):
    """Speech-to-text widget backed by the browser's Webkit Speech API.

    The widget exposes the ``transcript`` text along with the ``listening`` and
    ``trigger_listen`` booleans; it does not require initialization arguments.

    Examples:
        ```python
        speech = WebkitSpeechToTextWidget()
        speech
        ```
    """

    transcript = traitlets.Unicode("").tag(sync=True)
    listening = traitlets.Bool(False).tag(sync=True)
    trigger_listen = traitlets.Bool(False).tag(sync=True)
    _esm = Path(__file__).parent / "static" / "talk-widget.js"
    _css = Path(__file__).parent / "static" / "talk-widget.css"
