from pathlib import Path
from typing import Any, Optional, Tuple

import anywidget
import traitlets


_ESM_PATH = Path(__file__).parent / "static" / "circular-slider.js"
_CSS_PATH = Path(__file__).parent / "static" / "circular-slider.css"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _validate_size(size: int, thickness: int) -> None:
    """Make sure size is large enough to render at the chosen thickness.

    The track is a ring of width *thickness*; handles sit on top of the ring
    with a radius proportional to thickness. Below this minimum the handles
    swallow the track and the widget no longer looks like a slider.
    """
    minimum = 2 * thickness + 30
    if size < minimum:
        raise ValueError(
            f"size={size} is too small to render with thickness={thickness}. "
            f"Use size >= {minimum} (rule: size >= 2 * thickness + 30), "
            "or pass a smaller thickness."
        )


class CircularSlider(anywidget.AnyWidget):
    """Circular dial slider for selecting a single value.

    Mirrors ``mo.ui.slider`` semantics (``start``/``stop``/``step``/``value``)
    but lays the range out around a full circle. The ``start`` value sits at
    12 o'clock and values increase clockwise.

    Examples:
        ```python
        from wigglystuff import CircularSlider

        dial = CircularSlider(start=0, stop=100, step=1, value=42)
        dial
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    _mode = traitlets.Unicode("single").tag(sync=True)

    start = traitlets.Float(0.0).tag(sync=True)
    stop = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    value = traitlets.Float(0.0).tag(sync=True)
    size = traitlets.Int(220).tag(sync=True)
    thickness = traitlets.Int(18).tag(sync=True)
    show_value = traitlets.Bool(True).tag(sync=True)
    color = traitlets.Unicode("").tag(sync=True)
    label = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        start: float = 0.0,
        stop: float = 100.0,
        step: float = 1.0,
        value: Optional[float] = None,
        size: int = 220,
        thickness: int = 18,
        show_value: bool = True,
        color: str = "",
        label: str = "",
        **kwargs: Any,
    ) -> None:
        """Create a CircularSlider.

        Args:
            start: Lower bound of the mapped value range.
            stop: Upper bound of the mapped value range.
            step: Snap increment in value units (must be > 0).
            value: Initial value; defaults to ``start``. Clamped to ``[start, stop]``.
            size: Diameter in pixels.
            thickness: Ring track thickness in pixels.
            show_value: Render the current value as text below the dial.
            color: Optional CSS color (e.g. ``"#ef4444"``, ``"tomato"``) for the
                filled arc and handle border. Empty string uses the theme default.
            label: Optional text label shown above the dial. Empty string hides it.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if start >= stop:
            raise ValueError("start must be less than stop.")
        if step <= 0:
            raise ValueError("step must be positive.")
        _validate_size(size, thickness)
        if value is None:
            value = start
        value = _clamp(float(value), start, stop)
        super().__init__(
            _mode="single",
            start=float(start),
            stop=float(stop),
            step=float(step),
            value=value,
            size=size,
            thickness=thickness,
            show_value=show_value,
            color=color,
            label=label,
            **kwargs,
        )


class CircularRangeSlider(anywidget.AnyWidget):
    """Circular dial slider for selecting a span of values.

    Mirrors ``mo.ui.range_slider`` semantics but lays the range out around a
    full circle. ``value`` is a ``(low, high)`` tuple; both ends are draggable.

    Examples:
        ```python
        from wigglystuff import CircularRangeSlider

        span = CircularRangeSlider(start=0, stop=100, step=1, value=(20, 80))
        span
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    _mode = traitlets.Unicode("range").tag(sync=True)

    start = traitlets.Float(0.0).tag(sync=True)
    stop = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    value = traitlets.Tuple(traitlets.Float(), traitlets.Float()).tag(sync=True)
    size = traitlets.Int(220).tag(sync=True)
    thickness = traitlets.Int(18).tag(sync=True)
    show_value = traitlets.Bool(True).tag(sync=True)
    color = traitlets.Unicode("").tag(sync=True)
    label = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        start: float = 0.0,
        stop: float = 100.0,
        step: float = 1.0,
        value: Optional[Tuple[float, float]] = None,
        size: int = 220,
        thickness: int = 18,
        show_value: bool = True,
        color: str = "",
        label: str = "",
        **kwargs: Any,
    ) -> None:
        """Create a CircularRangeSlider.

        Args:
            start: Lower bound of the mapped value range.
            stop: Upper bound of the mapped value range.
            step: Snap increment in value units (must be > 0).
            value: Initial ``(low, high)`` tuple; defaults to ``(start, stop)``.
                Each end is clamped to ``[start, stop]``; if the pair is passed
                in the wrong order it is sorted. Note: at runtime, dragging the
                filled arc past the 12 o'clock seam can produce a wrap-around
                value where ``low > high`` — that's intentional and means the
                range crosses the seam (going clockwise from ``low`` through
                the ``stop``/``start`` boundary to ``high``).
            size: Diameter in pixels.
            thickness: Ring track thickness in pixels.
            show_value: Render the current ``low – high`` range as text below the dial.
            color: Optional CSS color (e.g. ``"#ef4444"``, ``"tomato"``) for the
                filled arc and handle border. Empty string uses the theme default.
            label: Optional text label shown above the dial. Empty string hides it.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if start >= stop:
            raise ValueError("start must be less than stop.")
        if step <= 0:
            raise ValueError("step must be positive.")
        _validate_size(size, thickness)
        if value is None:
            value = (start, stop)
        if len(value) != 2:
            raise ValueError("value must be a (low, high) tuple of length 2.")
        low = _clamp(float(value[0]), start, stop)
        high = _clamp(float(value[1]), start, stop)
        if low > high:
            low, high = high, low
        super().__init__(
            _mode="range",
            start=float(start),
            stop=float(stop),
            step=float(step),
            value=(low, high),
            size=size,
            thickness=thickness,
            show_value=show_value,
            color=color,
            label=label,
            **kwargs,
        )
