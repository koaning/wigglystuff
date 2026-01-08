"""PulsarChart widget for stacked waveform visualization."""

from pathlib import Path
from typing import Any, List, Optional, Union

import anywidget
import traitlets


class PulsarChart(anywidget.AnyWidget):
    """Stacked overlapping line charts creating a ridge/horizon effect.

    Inspired by the iconic PSR B1919+21 pulsar visualization from
    Joy Division's "Unknown Pleasures" album cover. Each row represents
    a waveform that can overlap with adjacent rows.

    Examples:
        ```python
        import pandas as pd
        import numpy as np

        # Generate sample waveform data
        n_rows = 40
        n_points = 100
        data = {}
        for i in range(n_points):
            col = []
            for j in range(n_rows):
                x = i / n_points * 4 * np.pi
                y = np.sin(x + j * 0.1) * np.random.uniform(0.5, 1.5)
                col.append(y)
            data[i] = col

        df = pd.DataFrame(data)
        df.index = range(10, 10 + n_rows)  # Custom index

        chart = PulsarChart(df, x_label="Time", y_label="Channel")
        chart
        ```
    """

    _esm = Path(__file__).parent / "static" / "pulsar-chart.js"
    _css = Path(__file__).parent / "static" / "pulsar-chart.css"

    # Internal data representation: list of {index, values, x_values} dicts
    data = traitlets.List([]).tag(sync=True)

    # X-coordinates (column names from DataFrame)
    x_values = traitlets.List([]).tag(sync=True)

    # Dimensions
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)

    # Visual styling
    overlap = traitlets.Float(0.5).tag(sync=True)
    stroke_width = traitlets.Float(1.5).tag(sync=True)
    fill_opacity = traitlets.Float(1.0).tag(sync=True)
    peak_scale = traitlets.Float(1.0).tag(sync=True)  # Multiplier for peak height

    # Axis labels
    x_label = traitlets.Unicode("").tag(sync=True)
    y_label = traitlets.Unicode("").tag(sync=True)

    # Selection state (synced back to Python)
    selected_index = traitlets.Any(None, allow_none=True).tag(sync=True)
    selected_row = traitlets.List([]).tag(sync=True)

    def __init__(
        self,
        df: Any,
        width: int = 600,
        height: int = 400,
        overlap: float = 0.5,
        stroke_width: float = 1.5,
        fill_opacity: float = 1.0,
        peak_scale: float = 1.0,
        x_label: str = "",
        y_label: str = "",
        **kwargs: Any,
    ) -> None:
        """Create a PulsarChart widget.

        Args:
            df: A pandas or polars DataFrame where each row is a waveform.
                The DataFrame index will be used as row labels on the y-axis.
            width: Chart width in pixels.
            height: Chart height in pixels.
            overlap: Amount of vertical overlap between rows (0.0 to 1.0).
            stroke_width: Line stroke width in pixels.
            fill_opacity: Opacity of the fill beneath each line (0.0 to 1.0).
            peak_scale: Multiplier for peak height (1.0 = default, 2.0 = double height).
            x_label: Label for the x-axis.
            y_label: Label for the y-axis.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        data, x_values = self._convert_dataframe(df)

        super().__init__(
            data=data,
            x_values=x_values,
            width=width,
            height=height,
            overlap=overlap,
            stroke_width=stroke_width,
            fill_opacity=fill_opacity,
            peak_scale=peak_scale,
            x_label=x_label,
            y_label=y_label,
            **kwargs,
        )

    def _convert_dataframe(self, df: Any) -> tuple[List[dict], List]:
        """Convert a DataFrame to the internal data format.

        Args:
            df: A pandas or polars DataFrame.

        Returns:
            Tuple of (data, x_values) where data is a list of dicts with
            'index' and 'values' keys, and x_values is the list of column names.
        """
        # Handle polars DataFrame
        if hasattr(df, "to_pandas"):
            df = df.to_pandas()

        # Extract x-coordinates from column names
        x_values = [
            c if not hasattr(c, "item") else c.item()
            for c in df.columns
        ]

        # Convert pandas DataFrame to list of dicts
        result = []
        for idx, row in df.iterrows():
            result.append({
                "index": idx if not hasattr(idx, "item") else idx.item(),
                "values": [
                    v if not hasattr(v, "item") else v.item()
                    for v in row.values
                ],
            })
        return result, x_values

    @traitlets.validate("overlap")
    def _validate_overlap(self, proposal: dict[str, Any]) -> float:
        """Ensure overlap is between 0 and 1."""
        value = proposal["value"]
        if not 0.0 <= value <= 1.0:
            raise traitlets.TraitError("Overlap must be between 0.0 and 1.0.")
        return value

    @traitlets.validate("fill_opacity")
    def _validate_fill_opacity(self, proposal: dict[str, Any]) -> float:
        """Ensure fill_opacity is between 0 and 1."""
        value = proposal["value"]
        if not 0.0 <= value <= 1.0:
            raise traitlets.TraitError("Fill opacity must be between 0.0 and 1.0.")
        return value
