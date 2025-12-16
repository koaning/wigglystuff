from pathlib import Path
from typing import Any

import anywidget
import traitlets


class Slider2D(anywidget.AnyWidget):
    """Two dimensional slider for simultaneous adjustments.

    Emits synchronized ``x``/``y`` floats that stay within configurable bounds
    while rendering to a pixel canvas sized via ``width``/``height``.

    Examples:
        ```python
        slider = Slider2D(x=0.5, y=0.5, x_bounds=(0.0, 1.0), y_bounds=(0.0, 1.0))
        slider
        ```
    """

    _esm = Path(__file__).parent / "static" / "2dslider.js"
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    x_bounds = (
        traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=(-1.0, 1.0)
        ).tag(sync=True)
    )
    y_bounds = (
        traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=(-1.0, 1.0)
        ).tag(sync=True)
    )
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: int = 400,
        height: int = 400,
        x_bounds: tuple[float, float] = (-1.0, 1.0),
        y_bounds: tuple[float, float] = (-1.0, 1.0),
        **kwargs: Any,
    ) -> None:
        """Create a Slider2D widget.

        Args:
            x: Initial x coordinate.
            y: Initial y coordinate.
            width: Canvas width in pixels.
            height: Canvas height in pixels.
            x_bounds: Min/max tuple for x.
            y_bounds: Min/max tuple for y.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            **kwargs,
        )

    @traitlets.validate("x_bounds", "y_bounds")
    def _valid_bounds(self, proposal: dict[str, Any]) -> tuple[float, float]:
        """Ensure min < max for bounds."""
        min_val, max_val = proposal["value"]
        if not (isinstance(min_val, float) and isinstance(max_val, float)):
            raise traitlets.TraitError("Bounds must be a tuple of two floats.")
        if min_val >= max_val:
            raise traitlets.TraitError("Min must be less than max in bounds.")
        return proposal["value"]
