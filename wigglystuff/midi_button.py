from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


_ESM_PATH = Path(__file__).parent / "static" / "midi-button.js"
_CSS_PATH = Path(__file__).parent / "static" / "midi-button.css"

_MODES = ("momentary", "toggle")


class MidiButton(anywidget.AnyWidget):
    """A button that you can press on-screen or bind to a hardware MIDI pad.

    Unlike :class:`Knob` / :class:`Fader` (which learn a continuous
    control-change), a ``MidiButton`` learns a MIDI **note** — the message a
    drum pad or launch button sends — and turns presses into an event or a
    latched on/off state.

    Two modes:

    - ``"momentary"`` (default): ``value`` is ``True`` only while the button is
      held (mouse down, or note-on until note-off). Every press also bumps
      ``press_timestamp`` so an ``observe`` handler fires even on repeated
      presses.
    - ``"toggle"``: each press flips ``value`` between ``True`` and ``False``;
      releases are ignored.

    The MIDI "learn" flow mirrors the Knob: click the small **MIDI** chip, then
    hit a pad on your hardware — the next note-on binds to this button. Bindings
    persist in browser localStorage (keyed by ``midi_key`` / ``label``) and use
    the Web MIDI API (Chromium browsers, secure context).

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import MidiButton

        trigger = mo.ui.anywidget(MidiButton(label="Fire", midi=True))
        trigger
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    # --- Output traitlets ---
    value = traitlets.Bool(False).tag(sync=True)
    # Bumped on every press (even repeats) so ``observe`` always fires.
    press_timestamp = traitlets.Float(0.0).tag(sync=True)
    # Note-on velocity (0-127) of the last press; 127 for an on-screen click.
    velocity = traitlets.Int(0).tag(sync=True)

    # --- Configuration traitlets ---
    label = traitlets.Unicode("").tag(sync=True)
    icon = traitlets.Unicode("").tag(sync=True)
    mode = traitlets.Unicode("momentary").tag(sync=True)
    size = traitlets.Int(64).tag(sync=True)
    color = traitlets.Unicode("").tag(sync=True)

    # MIDI: an Ableton-style "learn" binding to a hardware note (pad/button).
    midi = traitlets.Bool(True).tag(sync=True)
    midi_supported = traitlets.Bool(False).tag(sync=True)
    midi_learning = traitlets.Bool(False).tag(sync=True)
    midi_note = traitlets.Int(-1).tag(sync=True)
    midi_channel = traitlets.Int(-1).tag(sync=True)
    midi_device = traitlets.Unicode("").tag(sync=True)
    # Persistence: bindings are stored in browser localStorage under
    # ``wigglystuff-midi/{midi_scope}/{midi_key}``.
    midi_key = traitlets.Unicode("").tag(sync=True)
    midi_scope = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        label: str = "",
        icon: str = "",
        mode: str = "momentary",
        value: bool = False,
        size: int = 64,
        color: str = "",
        midi: bool = True,
        midi_note: int = -1,
        midi_channel: int = -1,
        midi_key: str = "",
        midi_scope: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Create a MidiButton.

        Args:
            label: Optional caption shown above the pad.
            icon: Glyph shown on the pad face. Either a built-in name
                (``"play"``, ``"pause"``, ``"stop"``, ``"record"``,
                ``"skip-back"``, ``"skip-forward"``, ``"circle"``, ``"square"``,
                ``"triangle"``, ``"heart"``, ``"star"``, ``"bell"``, ``"zap"``,
                ``"check"``, ``"x"``, ``"plus"``, ``"minus"``, ``"power"``,
                ``"mic"``, ``"music"``) or any literal string/emoji (e.g.
                ``"🔴"``). Empty falls back to ``label`` on the face.
            mode: ``"momentary"`` (``value`` is ``True`` only while held) or
                ``"toggle"`` (each press flips ``value``).
            value: Initial state. For ``"toggle"`` this is the starting on/off;
                for ``"momentary"`` it is the resting (unpressed) state, usually
                ``False``.
            size: Pad size in pixels (square).
            color: Optional CSS color for the pressed/active button. Empty
                string uses the theme default.
            midi: Show a "MIDI learn" chip (default ``True``). Click it, then hit
                a pad on your hardware; the next note-on message binds to this
                button. Uses the Web MIDI API (Chromium browsers, secure
                context). Read the binding back via ``midi_note`` /
                ``midi_channel`` / ``midi_device``. Pass ``False`` for a plain
                on-screen button with no MIDI chip.
            midi_note: Bind a note number (0-127) up front instead of learning
                it. ``-1`` (default) leaves it unbound.
            midi_channel: MIDI channel (0-15) for the binding, or ``-1`` for any.
            midi_key: localStorage key for persisting the learned binding across
                restarts. Defaults to ``label``. Empty (no label either)
                disables persistence.
            midi_scope: Namespace for the persisted binding, so different
                notebooks don't collide. Empty (default) uses the browser's URL
                path automatically; pass an explicit string to pin it.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if mode not in _MODES:
            raise ValueError(f"mode must be one of {_MODES}, got {mode!r}.")
        if midi_scope is None:
            midi_scope = ""

        super().__init__(
            label=label,
            icon=icon,
            mode=mode,
            value=bool(value),
            size=size,
            color=color,
            midi=midi,
            midi_note=midi_note,
            midi_channel=midi_channel,
            midi_key=midi_key,
            midi_scope=midi_scope,
            **kwargs,
        )
