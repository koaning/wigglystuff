from pathlib import Path
from typing import Any, Optional, Sequence

import anywidget
import traitlets

DEFAULT_ACTIONS = ["previous", "accept", "fail", "defer"]
DEFAULT_EXTRA_KEYBOARD_MAPPING = {"s": "save", "m": "mic"}


def _default_keyboard_mapping(actions: Sequence[str]) -> dict[str, str]:
    mapping = {
        str(index): action
        for index, action in enumerate(actions[:9], start=1)
    }
    return {**mapping, **DEFAULT_EXTRA_KEYBOARD_MAPPING}


def _default_gamepad_mapping(actions: Sequence[str]) -> dict[str, str]:
    mapping = {
        str(index): action
        for index, action in enumerate(actions)
    }
    next_button = len(mapping)
    mapping[str(next_button)] = "save"
    mapping[str(next_button + 1)] = "mic"
    return mapping


class AnnotationWidget(anywidget.AnyWidget):
    """Annotation input widget with buttons, keyboard shortcuts, gamepad, and speech-to-text.

    This widget provides a UI input surface for annotation workflows. It does
    NOT render the object being annotated — the notebook handles content
    display and reacts to the ``action`` traitlet.

    The ``action_timestamp`` traitlet changes on every action, even repeated
    ones, so ``observe`` always fires.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import AnnotationWidget

        widget = mo.ui.anywidget(AnnotationWidget())
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "annotation-widget.js"
    _css = Path(__file__).parent / "static" / "annotation-widget.css"

    # --- Output traitlets ---
    action = traitlets.Unicode("").tag(sync=True)
    action_timestamp = traitlets.Float(0.0).tag(sync=True)
    note = traitlets.Unicode("").tag(sync=True)
    listening = traitlets.Bool(False).tag(sync=True)

    disabled = traitlets.Bool(False).tag(sync=True)
    show_save = traitlets.Bool(True).tag(sync=True)

    # --- Configuration traitlets ---
    actions = traitlets.List(
        traitlets.Unicode(),
        default_value=DEFAULT_ACTIONS,
    ).tag(sync=True)

    keyboard_mapping = traitlets.Dict(default_value={}).tag(sync=True)

    gamepad_mapping = traitlets.Dict(default_value={}).tag(sync=True)

    debounce_ms = traitlets.Int(200).tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)

    def __init__(
        self,
        *,
        actions: Optional[Sequence[str]] = None,
        keyboard_mapping: Optional[dict[str, str]] = None,
        gamepad_mapping: Optional[dict[str, str]] = None,
        debounce_ms: Optional[int] = None,
        width: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        init_kwargs: dict[str, Any] = {}
        action_list = list(actions) if actions is not None else list(DEFAULT_ACTIONS)
        if actions is not None:
            init_kwargs["actions"] = action_list
        init_kwargs["keyboard_mapping"] = (
            _default_keyboard_mapping(action_list)
            if keyboard_mapping is None
            else dict(keyboard_mapping)
        )
        init_kwargs["gamepad_mapping"] = (
            _default_gamepad_mapping(action_list)
            if gamepad_mapping is None
            else dict(gamepad_mapping)
        )
        if debounce_ms is not None:
            init_kwargs["debounce_ms"] = debounce_ms
        if width is not None:
            init_kwargs["width"] = width
        super().__init__(**init_kwargs, **kwargs)
