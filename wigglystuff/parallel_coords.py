"""ParallelCoordinates widget -- HiPlot-style interactive parallel coordinates."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import anywidget
import traitlets


def _ts() -> float:
    """Return a monotonic timestamp to ensure traitlet change detection."""
    return time.monotonic()


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
    height = traitlets.Int(500).tag(sync=True)
    width = traitlets.Int(0).tag(sync=True)

    # Brush extents synced from JS (compact dict describing axis brush ranges)
    brush_extents = traitlets.Dict({}).tag(sync=True)

    # Accumulated filter rules synced from JS (each Keep/Exclude click)
    _filter_history = traitlets.List([]).tag(sync=True)

    # Signal traitlet for Python → JS action requests
    _action_request = traitlets.Dict({}).tag(sync=True)

    # UIDs synced from JS (HiPlot onChange events for Keep/Exclude/brush)
    filtered_uids = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    selected_uids = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)

    # Derived indices (computed from UIDs)
    filtered_indices = traitlets.List(traitlets.Int(), default_value=[])
    selected_indices = traitlets.List(traitlets.Int(), default_value=[])

    def __init__(
        self,
        data: Any = None,
        *,
        color_by: str = "",
        color_map: dict[str, str] | None = None,
        height: int = 500,
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

    @traitlets.observe("filtered_uids")
    def _on_filtered_uids(self, change: dict) -> None:
        uids = change["new"]
        if not uids:
            self.filtered_indices = list(range(len(self.data)))
        else:
            self.filtered_indices = sorted(int(uid) for uid in uids)

    @traitlets.observe("selected_uids")
    def _on_selected_uids(self, change: dict) -> None:
        uids = change["new"]
        if not uids:
            self.selected_indices = []
        else:
            self.selected_indices = sorted(int(uid) for uid in uids)

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

    @property
    def selections(self) -> list[dict]:
        """Return the full filtering state including the active brush.

        Returns a list of ``{"action": ..., "extents": ...}`` dicts.
        Completed Keep/Exclude steps come first, followed by a
        ``{"action": "current", "extents": ...}`` entry if there is an
        active brush on any axis.
        """
        result = list(self._filter_history)
        if self.brush_extents:
            result.append({"action": "current", "extents": dict(self.brush_extents)})
        return result

    def keep(self) -> None:
        """Trigger a Keep action on the current brush selection.

        Equivalent to clicking the Keep button in the UI. Rows outside
        the current brush are removed. The action and brush extents are
        recorded in :attr:`filter_history`.
        """
        self._action_request = {"action": "keep", "ts": _ts()}

    def exclude(self) -> None:
        """Trigger an Exclude action on the current brush selection.

        Equivalent to clicking the Exclude button in the UI. Rows inside
        the current brush are removed. The action and brush extents are
        recorded in :attr:`filter_history`.
        """
        self._action_request = {"action": "exclude", "ts": _ts()}

    def restore(self) -> None:
        """Restore all rows and clear the filter history.

        Equivalent to clicking the Restore button in the UI. All
        Keep/Exclude operations are undone and :attr:`filter_history`
        is reset to an empty list.
        """
        self._action_request = {"action": "restore", "ts": _ts()}


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
