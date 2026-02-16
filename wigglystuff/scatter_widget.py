"""Interactive scatter drawing widget for painting labeled 2D datasets."""

from pathlib import Path
from typing import Any

import anywidget
import traitlets


class ScatterWidget(anywidget.AnyWidget):
    """Interactive scatter drawing widget for painting multi-class 2D data points.

    The widget renders a D3-powered SVG canvas where you can paint data points
    using a configurable brush. Points are grouped by class (color) and batch,
    making it easy to generate labeled 2D datasets interactively.

    Examples:
        ```python
        from wigglystuff import ScatterWidget

        widget = ScatterWidget(n_classes=3)
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "scatter-widget.js"
    _css = Path(__file__).parent / "static" / "scatter-widget.css"

    data = traitlets.List([]).tag(sync=True)
    brushsize = traitlets.Int(40).tag(sync=True)
    width = traitlets.Int(800).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    n_classes = traitlets.Int(4).tag(sync=True)

    def __init__(
        self,
        *,
        n_classes: int = 4,
        brushsize: int = 40,
        width: int = 800,
        height: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create a ScatterWidget.

        Args:
            n_classes: Number of point classes (1-4). Each class gets a
                distinct color and label.
            brushsize: Initial brush radius in pixels.
            width: SVG viewBox width in pixels.
            height: SVG viewBox height in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.

        Raises:
            ValueError: If *n_classes* is not between 1 and 4.
        """
        if not 1 <= n_classes <= 4:
            raise ValueError("n_classes must be between 1 and 4")
        super().__init__(
            n_classes=n_classes,
            brushsize=brushsize,
            width=width,
            height=height,
            **kwargs,
        )

    @traitlets.validate("n_classes")
    def _validate_n_classes(self, proposal: dict[str, Any]) -> int:
        """Ensure ``n_classes`` remains between 1 and 4."""
        value = proposal["value"]
        if not 1 <= value <= 4:
            raise traitlets.TraitError("n_classes must be between 1 and 4")
        return value

    @property
    def data_as_pandas(self):
        """Return the drawn points as a :class:`pandas.DataFrame`.

        Columns: ``x``, ``y``, ``color``, ``label``, ``batch``.
        """
        import pandas as pd

        return pd.DataFrame(self.data)

    @property
    def data_as_polars(self):
        """Return the drawn points as a :class:`polars.DataFrame`.

        Columns: ``x``, ``y``, ``color``, ``label``, ``batch``.
        """
        import polars as pl

        return pl.DataFrame(self.data)

    @property
    def data_as_X_y(self):
        """Return the drawn points as a ``(X, y)`` tuple of numpy arrays.

        When configured with ``n_classes=1`` (regression scenario), returns
        ``X`` with shape ``(n, 1)`` containing ``x`` values and ``y``
        as the target array.

        When configured with ``n_classes>1`` (classification scenario),
        returns ``X`` with shape ``(n, 2)`` containing ``(x, y)``
        coordinates and ``y`` as a list of color strings.
        """
        import numpy as np

        if self.n_classes == 1:
            if not self.data:
                return np.empty((0, 1)), np.array([])
            X = np.array([[d["x"]] for d in self.data])
            y = np.array([d["y"] for d in self.data])
            return X, y

        if not self.data:
            return np.empty((0, 2)), []
        X = np.array([[d["x"], d["y"]] for d in self.data])
        colors = [d["color"] for d in self.data]
        return X, colors
