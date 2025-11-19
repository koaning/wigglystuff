from pathlib import Path

import anywidget
import traitlets


class WebkitSpeechToTextWidget(anywidget.AnyWidget):
    """Speech-to-text widget backed by the browser's Webkit Speech API."""

    transcript = traitlets.Unicode("").tag(sync=True)
    listening = traitlets.Bool(False).tag(sync=True)
    trigger_listen = traitlets.Bool(False).tag(sync=True)
    _esm = Path(__file__).parent / "static" / "talk-widget.js"
    _css = Path(__file__).parent / "static" / "talk-widget.css"
