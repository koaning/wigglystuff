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


class AnnotationWidget(anywidget.AnyWidget):
    """Annotation input widget with buttons, keyboard shortcuts, gamepad, and speech-to-text.

    This widget provides a UI input surface for annotation workflows. It does
    NOT render the object being annotated — the notebook handles content
    display and reacts to the ``action`` traitlet.

    The ``action_timestamp`` traitlet changes on every action, even repeated
    ones, so ``observe`` always fires.

    Examples:
        ```python
        from wigglystuff import AnnotationWidget

        widget = AnnotationWidget()
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

    gamepad_mapping = traitlets.Dict(
        default_value={
            "0": "accept",
            "1": "fail",
            "2": "defer",
            "3": "previous",
            "4": "save",
            "5": "mic",
        },
    ).tag(sync=True)

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
        if actions is not None:
            init_kwargs["actions"] = list(actions)
        if keyboard_mapping is not None:
            init_kwargs["keyboard_mapping"] = dict(keyboard_mapping)
        if gamepad_mapping is not None:
            init_kwargs["gamepad_mapping"] = dict(gamepad_mapping)
        if debounce_ms is not None:
            init_kwargs["debounce_ms"] = debounce_ms
        if width is not None:
            init_kwargs["width"] = width
        super().__init__(**init_kwargs, **kwargs)
        self._keyboard_mapping_is_default = keyboard_mapping is None
        if self._keyboard_mapping_is_default:
            self._set_default_keyboard_mapping()

    def _set_default_keyboard_mapping(self) -> None:
        self._setting_default_keyboard_mapping = True
        self.keyboard_mapping = _default_keyboard_mapping(self.actions or [])
        self._setting_default_keyboard_mapping = False

    @traitlets.observe("actions")
    def _update_default_keyboard_mapping(self, change: dict[str, Any]) -> None:
        if getattr(self, "_keyboard_mapping_is_default", False):
            self._set_default_keyboard_mapping()

    @traitlets.observe("keyboard_mapping")
    def _mark_custom_keyboard_mapping(self, change: dict[str, Any]) -> None:
        if getattr(self, "_setting_default_keyboard_mapping", False):
            return
        if hasattr(self, "_keyboard_mapping_is_default"):
            self._keyboard_mapping_is_default = False
