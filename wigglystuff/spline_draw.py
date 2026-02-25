"""SplineDraw widget -- ScatterWidget with Python-computed spline curve overlay."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import anywidget
import numpy as np
import traitlets


def _gaussian_smooth(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Default spline function using Gaussian kernel smoothing (Nadaraya-Watson).

    Bandwidth auto-scales to 1/20th of the x-range. Requires only numpy.
    """
    if len(x) < 2:
        return x, y
    x_eval = np.linspace(x.min(), x.max(), 200)
    bandwidth = (x.max() - x.min()) / 20
    if bandwidth == 0:
        return x_eval, np.full_like(x_eval, y.mean())
    diff = x_eval[:, None] - x[None, :]
    weights = np.exp(-0.5 * (diff / bandwidth) ** 2)
    weights /= weights.sum(axis=1, keepdims=True)
    return x_eval, weights @ y


class SplineDraw(anywidget.AnyWidget):
    """Draw scatter points and see a spline curve fitted through them.

    This widget is built on the same D3/SVG canvas as ScatterWidget. The spline
    is computed by a Python callback function. Pass any callable with signature
    ``(x, y) -> (x_curve, y_curve)`` where inputs and outputs are 1-D numpy
    arrays. A built-in Gaussian kernel smoother is used when no function is
    provided.

    Examples:
        ```python
        from wigglystuff import SplineDraw

        widget = SplineDraw()
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "spline-draw.js"
    _css = Path(__file__).parent / "static" / "spline-draw.css"

    data = traitlets.List([]).tag(sync=True)
    brushsize = traitlets.Int(40).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    n_classes = traitlets.Int(1).tag(sync=True)

    curve = traitlets.List([]).tag(sync=True)
    curve_error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        spline_fn: Callable | None = None,
        *,
        n_classes: int = 1,
        brushsize: int = 40,
        width: int = 600,
        height: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create a SplineDraw widget.

        Args:
            spline_fn: A callable ``(x, y) -> (x_curve, y_curve)`` where
                inputs are 1-D numpy arrays of drawn point coordinates and
                outputs are 1-D numpy arrays defining the fitted curve.
                Defaults to a Gaussian kernel smoother.
            n_classes: Number of point classes (1-4). Defaults to 1.
            brushsize: Initial brush radius in pixels.
            width: SVG viewBox width in pixels.
            height: SVG viewBox height in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if not 1 <= n_classes <= 4:
            raise ValueError("n_classes must be between 1 and 4")
        self._spline_fn = spline_fn or _gaussian_smooth
        super().__init__(
            n_classes=n_classes,
            brushsize=brushsize,
            width=width,
            height=height,
            **kwargs,
        )
        self.observe(self._recompute_curve, names=["data"])

    @traitlets.validate("n_classes")
    def _validate_n_classes(self, proposal: dict[str, Any]) -> int:
        """Ensure ``n_classes`` remains between 1 and 4."""
        value = proposal["value"]
        if not 1 <= value <= 4:
            raise traitlets.TraitError("n_classes must be between 1 and 4")
        return value

    def _recompute_curve(self, change: Any = None) -> None:
        """Call spline_fn per class on current data and update the curve traitlet."""
        if len(self.data) < 2:
            self.curve = []
            self.curve_error = ""
            return

        # Group data by color
        groups: dict[str, list[dict]] = {}
        for pt in self.data:
            groups.setdefault(pt.get("color", ""), []).append(pt)

        curves = []
        errors = []
        for color, pts in groups.items():
            if len(pts) < 2:
                continue
            try:
                x = np.array([p["x"] for p in pts])
                y = np.array([p["y"] for p in pts])
                x_curve, y_curve = self._spline_fn(x, y)
                curves.append({
                    "color": color,
                    "points": [
                        {"x": float(xv), "y": float(yv)}
                        for xv, yv in zip(x_curve, y_curve)
                    ],
                })
            except Exception as exc:
                errors.append(f"{color}: {exc}")

        self.curve = curves
        self.curve_error = "; ".join(errors) if errors else ""

    @property
    def curve_as_numpy(self) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        """Return fitted curves as a dict keyed by color.

        Each value is an ``(x_array, y_array)`` tuple of numpy arrays.
        With a single class the dict has one entry.
        """
        result = {}
        for entry in self.curve:
            pts = entry.get("points", [])
            if pts:
                result[entry["color"]] = (
                    np.array([p["x"] for p in pts]),
                    np.array([p["y"] for p in pts]),
                )
        return result

    @property
    def data_as_numpy(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the drawn points as ``(x_array, y_array)`` numpy arrays."""
        if not self.data:
            return np.array([]), np.array([])
        return (
            np.array([pt["x"] for pt in self.data]),
            np.array([pt["y"] for pt in self.data]),
        )

    @property
    def data_as_pandas(self):
        """Return the drawn points as a :class:`pandas.DataFrame`."""
        import pandas as pd

        return pd.DataFrame(self.data)

    @property
    def data_as_polars(self):
        """Return the drawn points as a :class:`polars.DataFrame`."""
        import polars as pl

        return pl.DataFrame(self.data)

    @property
    def data_as_X_y(self):
        """Return the drawn points as a ``(X, y)`` tuple of numpy arrays.

        With ``n_classes=1`` returns X of shape ``(n, 1)`` with x values
        and y as target. With ``n_classes>1`` returns X of shape ``(n, 2)``
        and y as color strings.
        """
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
