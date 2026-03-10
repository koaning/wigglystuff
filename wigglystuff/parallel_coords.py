"""ParallelCoordinates widget -- HiPlot-style interactive parallel coordinates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anywidget
import traitlets


class ParallelCoordinates(anywidget.AnyWidget):
    """Interactive parallel coordinates plot powered by HiPlot.

    Wraps Facebook Research's HiPlot library to provide brush filtering on
    axes, axis reordering via drag, and coloring lines by a selected
    dimension -- all inside a notebook widget.

    Args:
        data: Dataset as a list of dictionaries, pandas DataFrame, or polars
            DataFrame. Each row becomes one polyline in the chart.
        color_by: Column name used to color lines. Leave empty for a single
            default color.
        color_map: Mapping of categorical values to CSS colors (e.g.
            ``{"a": "red", "b": "#0000ff"}``). Values not in the map use the
            default palette. Colors are auto-converted to ``rgb(...)`` format.
        height: Widget height in pixels.
        width: Widget width in pixels. Set to 0 for container width.
        ignore: Column names to exclude from the plot.

    Examples:
        ```python
        from wigglystuff import ParallelCoordinates
        import polars as pl

        df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [5, 4, 3, 2, 1],
            "label": ["a", "a", "b", "b", "b"],
        })
        widget = ParallelCoordinates(df, color_by="label", color_map={"a": "red"})
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "parallel-coords.js"
    _css = Path(__file__).parent / "static" / "parallel-coords.css"

    data = traitlets.List([]).tag(sync=True)
    color_by = traitlets.Unicode("").tag(sync=True)
    color_map = traitlets.Dict({}).tag(sync=True)
    height = traitlets.Int(600).tag(sync=True)
    width = traitlets.Int(0).tag(sync=True)

    # Brush extents synced from JS (compact dict, works at any dataset size)
    brush_extents = traitlets.Dict({}).tag(sync=True)

    # Computed Python-side from brush_extents (no longer synced from JS)
    filtered_indices = traitlets.List(traitlets.Int(), default_value=[])
    selected_indices = traitlets.List(traitlets.Int(), default_value=[])

    def __init__(
        self,
        data=None,
        *,
        color_by: str = "",
        color_map: dict[str, str] | None = None,
        height: int = 600,
        width: int = 0,
        ignore: list[str] | None = None,
    ) -> None:
        """Create a ParallelCoordinates widget.

        Args:
            data: Dataset as a list of dicts, pandas DataFrame, or polars
                DataFrame. Each dict/row is one data point.
            color_by: Column name to color lines by. Empty string for uniform
                color.
            color_map: Mapping of categorical values to CSS colors (e.g.
                ``{"a": "red", "b": "#0000ff"}``). Values not in the map use
                the default palette.
            height: Widget height in pixels.
            width: Widget width in pixels. Set to 0 for container width.
            ignore: Column names to exclude from the plot.
        """
        records = _to_records(data)
        if ignore:
            records = [
                {k: v for k, v in row.items() if k not in ignore}
                for row in records
            ]
        filtered_indices = list(range(len(records)))
        super().__init__(
            data=records,
            color_by=color_by,
            color_map=color_map or {},
            height=height,
            width=width,
            filtered_indices=filtered_indices,
            selected_indices=[],
        )

    @traitlets.observe("brush_extents")
    def _recompute_indices(self, change: dict) -> None:
        extents = change["new"]
        if not extents:
            indices = list(range(len(self.data)))
        else:
            indices = []
            for i, row in enumerate(self.data):
                if _row_passes(row, extents):
                    indices.append(i)
        self.filtered_indices = indices
        self.selected_indices = indices

    @property
    def filtered_data(self) -> list[dict]:
        """Return the subset of data rows passing all brush filters."""
        return [self.data[i] for i in self.filtered_indices]

    @property
    def filtered_as_pandas(self):
        """Return filtered data as a :class:`pandas.DataFrame`."""
        import pandas as pd

        return pd.DataFrame(self.filtered_data)

    @property
    def filtered_as_polars(self):
        """Return filtered data as a :class:`polars.DataFrame`."""
        import polars as pl

        return pl.DataFrame(self.filtered_data)

    @property
    def selected_data(self) -> list[dict]:
        """Return the subset of data rows that are selected."""
        return [self.data[i] for i in self.selected_indices]


def _row_passes(row: dict, extents: dict) -> bool:
    """Return True if *row* satisfies every brush extent (AND logic)."""
    for col, ext in extents.items():
        value = row.get(col)
        if value is None:
            return False
        ext_type = ext.get("type", "")
        if ext_type == "categorical":
            if str(value) not in ext.get("values", []):
                return False
        elif ext_type in ("numeric", "numericlog", "numericpercentile"):
            rng = ext.get("range", [])
            if len(rng) == 2:
                lo, hi = min(rng), max(rng)
                try:
                    if not (lo <= float(value) <= hi):
                        return False
                except (ValueError, TypeError):
                    return False
    return True


def _to_records(data: Any) -> list[dict]:
    """Convert data to list of plain dicts, handling DataFrames and numpy types."""
    if data is None:
        return []
    # polars DataFrame (check first -- polars also has .to_dict)
    if hasattr(data, "to_dicts") and callable(data.to_dicts):
        records = data.to_dicts()
    # pandas DataFrame
    elif hasattr(data, "to_dict") and callable(data.to_dict):
        records = data.to_dict("records")
    elif isinstance(data, list):
        records = list(data)
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")
    # Coerce numpy scalar types to Python natives for JSON serialization
    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if hasattr(v, "item"):
                clean_row[k] = v.item()
            else:
                clean_row[k] = v
        cleaned.append(clean_row)
    return cleaned
