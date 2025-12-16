from pathlib import Path

import anywidget
import traitlets


class GamepadWidget(anywidget.AnyWidget):
    """Listen to browser gamepad events and sync state back to Python.

    This widget does not require any initialization arguments; all state is
    mirrored through traitlets such as ``axes`` and ``current_button_press``.

    Examples:
        ```python
        gamepad = GamepadWidget()
        gamepad
        ```
    """

    _esm = Path(__file__).parent / "static" / "gamepad-widget.js"
    current_button_press = traitlets.Int(-1).tag(sync=True)
    current_timestamp = traitlets.Float(0.0).tag(sync=True)
    previous_timestamp = traitlets.Float(0.0).tag(sync=True)
    axes = traitlets.List(trait=traitlets.Float(), default_value=[0.0, 0.0, 0.0, 0.0]).tag(
        sync=True
    )
    dpad_up = traitlets.Bool(False).tag(sync=True)
    dpad_down = traitlets.Bool(False).tag(sync=True)
    dpad_left = traitlets.Bool(False).tag(sync=True)
    dpad_right = traitlets.Bool(False).tag(sync=True)
    button_id = traitlets.Int(0).tag(sync=True)
