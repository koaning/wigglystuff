"""AltairWidget for flicker-free Altair chart updates."""

from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


class AltairWidget(anywidget.AnyWidget):
    """Flicker-free Altair chart widget.

    Wraps an Altair chart and uses the Vega View API to update data in-place
    when only the data portion of the spec changes, avoiding full DOM rebuilds.

    The widget should be created once and then updated via the ``chart`` setter
    from a reactive cell. This keeps the DOM element stable and allows the
    JavaScript side to detect data-only changes and apply them smoothly.

    Examples:
        ```python
        import altair as alt
        import pandas as pd
        from wigglystuff import AltairWidget

        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        chart = alt.Chart(df).mark_point().encode(x="x", y="y")
        widget = AltairWidget(chart)
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "altair-widget.js"
    _css = Path(__file__).parent / "static" / "altair-widget.css"

    spec = traitlets.Dict({}).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)

    def __init__(
        self,
        chart: Any = None,
        *,
        width: int = 600,
        height: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create an AltairWidget.

        Args:
            chart: An Altair chart object or a Vega-Lite spec dict. If ``None``,
                the widget starts empty and can be populated later via the
                ``chart`` setter.
            width: Container width in pixels.
            height: Container height in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        spec = {}
        if chart is not None:
            spec = self._chart_to_spec(chart)
        super().__init__(
            spec=spec,
            width=width,
            height=height,
            **kwargs,
        )

    @property
    def chart(self):
        """Write-only convenience property. Read ``widget.spec`` instead."""
        raise AttributeError(
            "chart is write-only. Read the spec dict via widget.spec instead."
        )

    @chart.setter
    def chart(self, value: Any) -> None:
        """Accept an Altair chart object or dict and update the spec."""
        self.spec = self._chart_to_spec(value)

    @staticmethod
    def _chart_to_spec(chart: Any) -> dict:
        """Convert an Altair chart or dict to a Vega-Lite spec dict."""
        if isinstance(chart, dict):
            return chart
        if hasattr(chart, "to_dict"):
            return chart.to_dict()
        raise TypeError(
            f"Expected an Altair chart or dict, got {type(chart).__name__}"
        )
