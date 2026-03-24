from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


class PlaySlider(anywidget.AnyWidget):
    """Slider with a play/pause button that auto-advances at a configurable pace.

    Examples:
        ```python
        from wigglystuff import PlaySlider

        slider = PlaySlider(min_value=0, max_value=50, step=1, interval_ms=300)
        slider
        ```
    """

    _esm = Path(__file__).parent / "static" / "play-slider.js"
    _css = Path(__file__).parent / "static" / "play-slider.css"

    value = traitlets.Float(0.0).tag(sync=True)
    min_value = traitlets.Float(0.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    interval_ms = traitlets.Int(200).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
    loop = traitlets.Bool(False).tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)

    def __init__(
        self,
        value: Optional[float] = None,
        min_value: float = 0.0,
        max_value: float = 100.0,
        step: float = 1.0,
        interval_ms: int = 200,
        loop: bool = False,
        width: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create a PlaySlider.

        Args:
            value: Starting position; defaults to *min_value*.
            min_value: Lower bound.
            max_value: Upper bound.
            step: Increment per tick.
            interval_ms: Milliseconds between auto-advance ticks.
            loop: Wrap to *min_value* when reaching the end instead of stopping.
            width: Widget width in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value.")
        if step <= 0:
            raise ValueError("step must be positive.")
        if value is None:
            value = min_value
        super().__init__(
            value=value,
            min_value=min_value,
            max_value=max_value,
            step=step,
            interval_ms=interval_ms,
            loop=loop,
            width=width,
            **kwargs,
        )

    @property
    def values(self):
        """All discrete values from min_value to max_value (inclusive) at the current step."""
        step_str = str(self.step)
        precision = len(step_str.rstrip("0").split(".")[-1]) if "." in step_str else 0
        result = []
        v = self.min_value
        while v <= self.max_value:
            result.append(round(v, precision))
            v += self.step
        return result
