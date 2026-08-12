from pathlib import Path
from typing import Any, Optional, Sequence

import anywidget
import traitlets

from ._controls import TickSpec, clamp, normalize_steps, normalize_ticks


_ESM_PATH = Path(__file__).parent / "static" / "fader.js"
_CSS_PATH = Path(__file__).parent / "static" / "fader.css"

_ORIENTATIONS = ("vertical", "horizontal")


class Fader(anywidget.AnyWidget):
    """Mixing-console style fader: a cap that slides along a track.

    A linear slider drawn to look like a channel fader, with a configurable
    tick scale (e.g. dB marks) alongside the track. Vertical by default, with
    ``max_value`` at the top; pass ``orientation="horizontal"`` for a
    left-to-right fader.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import Fader

        level = mo.ui.anywidget(
            Fader(min_value=-60, max_value=6, value=0, ticks=[-60, -20, -6, 0, 6],
                  label="Level")
        )
        level
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    value = traitlets.Float(0.0).tag(sync=True)
    min_value = traitlets.Float(0.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    ticks = traitlets.List(traitlets.Dict()).tag(sync=True)
    # Discrete detents to snap to; empty means continuous (use ``step``).
    steps = traitlets.List(traitlets.Float(), default_value=[]).tag(sync=True)
    orientation = traitlets.Unicode("vertical").tag(sync=True)
    length = traitlets.Int(200).tag(sync=True)
    label = traitlets.Unicode("").tag(sync=True)
    show_value = traitlets.Bool(True).tag(sync=True)
    color = traitlets.Unicode("").tag(sync=True)

    # MIDI: an Ableton-style "learn" binding to a hardware control-change (CC).
    midi = traitlets.Bool(False).tag(sync=True)
    midi_supported = traitlets.Bool(False).tag(sync=True)
    midi_learning = traitlets.Bool(False).tag(sync=True)
    midi_cc = traitlets.Int(-1).tag(sync=True)
    midi_channel = traitlets.Int(-1).tag(sync=True)
    midi_device = traitlets.Unicode("").tag(sync=True)
    # Persistence: bindings are stored in browser localStorage under
    # ``wigglystuff-midi/{midi_scope}/{midi_key}``.
    midi_key = traitlets.Unicode("").tag(sync=True)
    midi_scope = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        value: Optional[float] = None,
        min_value: float = 0.0,
        max_value: float = 100.0,
        step: float = 1.0,
        ticks: TickSpec = None,
        steps: Optional[Sequence[Any]] = None,
        orientation: str = "vertical",
        length: int = 200,
        label: str = "",
        show_value: bool = True,
        color: str = "",
        midi: bool = False,
        midi_cc: int = -1,
        midi_channel: int = -1,
        midi_key: str = "",
        midi_scope: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Create a Fader.

        Args:
            value: Initial value; defaults to ``min_value``. Clamped to range.
            min_value: Lower bound of the value range (bottom / left).
            max_value: Upper bound of the value range (top / right).
            step: Snap increment in value units (must be > 0).
            ticks: Tick/scale marks. ``None`` for none, an int ``N`` for ``N``
                evenly spaced ticks, a list of values, or a list of
                ``(value, label)`` pairs.
            steps: Discrete detents to snap to (a stepped fader). Same shape as
                ``ticks`` — numbers or ``(value, label)`` pairs. When given,
                ``min_value``/``max_value`` are derived from the steps, the
                detents double as the ticks, and dragging snaps to the nearest
                one. Mutually exclusive with ``ticks``.
            orientation: ``"vertical"`` (default) or ``"horizontal"``.
            length: Track length in pixels (the long dimension).
            label: Optional text label shown above the fader.
            show_value: Render the current value as text next to the fader.
            color: Optional CSS color for the filled track and cap. Empty
                string uses the theme default.
            midi: Show a "MIDI learn" button. Click it, then move a control on
                your hardware; the next control-change (CC) message binds to
                this fader and drives its value. Uses the Web MIDI API (Chromium
                browsers, secure context). Read the binding back via
                ``midi_cc`` / ``midi_channel`` / ``midi_device``.
            midi_cc: Bind a control-change number (0-127) up front instead of
                learning it. ``-1`` (default) leaves it unbound.
            midi_channel: MIDI channel (0-15) for the binding, or ``-1`` for any.
            midi_key: localStorage key for persisting the learned binding across
                restarts. Defaults to ``label``. Empty (no label either) disables
                persistence.
            midi_scope: Namespace for the persisted binding, so different
                notebooks don't collide. Empty (default) uses the browser's URL
                path automatically; pass an explicit string to pin it (or to
                intentionally share a mapping across notebooks).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if midi_scope is None:
            midi_scope = ""
        if step <= 0:
            raise ValueError("step must be positive.")
        if orientation not in _ORIENTATIONS:
            raise ValueError(
                f"orientation must be one of {_ORIENTATIONS}, got {orientation!r}."
            )

        if steps is not None:
            if ticks is not None:
                raise ValueError("`ticks` is mutually exclusive with `steps`.")
            step_values = normalize_steps(steps)
            min_value, max_value = step_values[0], step_values[-1]
            tick_dicts = normalize_ticks(steps, min_value, max_value)
            if value is None:
                value = step_values[0]
            else:
                value = min(step_values, key=lambda s: abs(s - float(value)))
        else:
            step_values = []
            if min_value >= max_value:
                raise ValueError("min_value must be less than max_value.")
            tick_dicts = normalize_ticks(ticks, min_value, max_value)
            if value is None:
                value = min_value
            value = clamp(float(value), min_value, max_value)

        super().__init__(
            value=float(value),
            min_value=float(min_value),
            max_value=float(max_value),
            step=float(step),
            ticks=tick_dicts,
            steps=step_values,
            orientation=orientation,
            length=length,
            label=label,
            show_value=show_value,
            color=color,
            midi=midi,
            midi_cc=midi_cc,
            midi_channel=midi_channel,
            midi_key=midi_key,
            midi_scope=midi_scope,
            **kwargs,
        )
