"""Scalable, linked scatterplot matrix for numeric tabular data."""

from __future__ import annotations

import colorsys
from pathlib import Path
from typing import Any, Mapping, Sequence

import anywidget
import traitlets


# Eight categorical hues, in an order checked for colour-vision-deficiency
# separation between neighbours. The frontend swaps in dark-surface steps of
# the same hues when the notebook is dark.
_DEFAULT_COLORS = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#6250d6",
    "#e34948",
]


class PairPlot(anywidget.AnyWidget):
    """Interactive scatterplot matrix with linked box and lasso selection.

    ``PairPlot`` sends numeric data to the browser as binary float32 data and
    keeps the full matrix in a Web Worker.  The visible plot is bounded by a
    global mark budget, while a selection is evaluated against every row.

    Args:
        data: A two-dimensional NumPy array, pandas DataFrame, or polars
            DataFrame containing numeric dimensions.
        columns: Labels for NumPy columns, or the DataFrame columns to display.
            NumPy columns default to ``x0``, ``x1``, ...; DataFrames default to
            every numeric column except a named ``color`` column.
        color: Optional categorical values with one entry per row.  For a
            DataFrame this may instead be the name of a color column.
        color_map: Optional mapping from category values to CSS colors.
        layout: ``"full"`` or ``"lower"``.
        mode: Selection tool, ``"box"`` or ``"lasso"``. A box can be dragged
            to a new spot after it is drawn; both are switchable in the widget.
        cell_size: Size of each matrix cell in CSS pixels. ``None`` (the
            default) fits the matrix to the available width.
        max_marks: Approximate maximum number of point marks rendered across
            all visible off-diagonal cells.
        point_size: Point diameter in CSS pixels. ``None`` (the default)
            picks a size and opacity from how many points share a cell.

    The selection is synced as a compact data-coordinate description (box
    corners or lasso vertices). Use :meth:`get_mask`, :meth:`get_indices`, or
    :attr:`selected_data` to obtain exact Python-side results without syncing
    a potentially huge index list.

    Like HiPlot, a selection can be turned into a filter: **Keep** drops every
    row outside it and **Exclude** drops every row inside it, after which the
    axes rescale to the rows that remain. Filters stack, are synced as the
    replayable ``filters`` list, and **Reset** removes them all. The same
    actions are available from Python as :meth:`keep`, :meth:`exclude`, and
    :meth:`reset`; :attr:`active_data` holds the rows that survive the filters.
    """

    _esm = Path(__file__).parent / "static" / "pair-plot.js"
    _css = Path(__file__).parent / "static" / "pair-plot.css"

    columns = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    categories = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    palette = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    layout = traitlets.Enum(["full", "lower"], default_value="full").tag(sync=True)
    mode = traitlets.Enum(["box", "lasso"], default_value="box").tag(sync=True)
    cell_size = traitlets.Int(None, allow_none=True, min=40).tag(sync=True)
    max_marks = traitlets.Int(2_000_000, min=10_000).tag(sync=True)
    point_size = traitlets.Float(None, allow_none=True, min=0.25).tag(sync=True)

    selection = traitlets.Dict(default_value={}).tag(sync=True)
    filters = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)
    selected_count = traitlets.Int(0, min=0).tag(sync=True)
    status = traitlets.Unicode("loading").tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)
    data_version = traitlets.Int(0).tag(sync=True)

    def __init__(
        self,
        data: Any,
        *,
        columns: Sequence[str] | None = None,
        color: Any = None,
        color_map: Mapping[Any, str] | None = None,
        layout: str = "full",
        mode: str = "box",
        cell_size: int | None = None,
        max_marks: int = 2_000_000,
        point_size: float | None = None,
        **kwargs: Any,
    ) -> None:
        matrix, names, color_values, source_kind = _normalize_input(
            data, columns=columns, color=color
        )
        codes, category_labels, palette = _encode_colors(
            color_values, color_map, matrix.shape[0]
        )

        self._source_data = data
        self._source_kind = source_kind
        self._matrix = matrix
        self._color_codes = codes

        super().__init__(
            columns=names,
            categories=category_labels,
            palette=palette,
            layout=layout,
            mode=mode,
            cell_size=cell_size,
            max_marks=max_marks,
            point_size=point_size,
            **kwargs,
        )
        self.on_msg(self._handle_frontend_message)

    @property
    def shape(self) -> tuple[int, int]:
        """The numeric matrix shape as ``(rows, dimensions)``."""
        return tuple(self._matrix.shape)

    def set_data(
        self,
        data: Any,
        *,
        columns: Sequence[str] | None = None,
        color: Any = None,
        color_map: Mapping[Any, str] | None = None,
    ) -> None:
        """Replace the displayed dataset and clear the current selection."""
        matrix, names, color_values, source_kind = _normalize_input(
            data, columns=columns, color=color
        )
        codes, category_labels, palette = _encode_colors(
            color_values, color_map, matrix.shape[0]
        )

        self._source_data = data
        self._source_kind = source_kind
        self._matrix = matrix
        self._color_codes = codes
        self.columns = names
        self.categories = category_labels
        self.palette = palette
        self.filters = []
        self.clear_selection()
        self.status = "loading"
        self.error = ""
        # Each view answers a data_version bump with a "ready" message, which
        # makes Python send the new buffers.
        self.data_version += 1

    def clear_selection(self) -> None:
        """Clear the selection and restore the unfiltered color display."""
        self.selection = {}
        self.selected_count = 0

    def _selection_mask(self, selection: Mapping[str, Any]):
        """Rows inside a box or lasso selection dict, ignoring filters."""
        import numpy as np

        n_rows, n_dims = self._matrix.shape
        mask = np.zeros(n_rows, dtype=bool)
        kind = selection.get("type")
        if kind not in ("box", "lasso"):
            return mask
        x_index = int(selection.get("x_index", -1))
        y_index = int(selection.get("y_index", -1))
        if not (0 <= x_index < n_dims and 0 <= y_index < n_dims):
            return mask

        # Compare in float64, like the browser does, so counts match exactly.
        x = self._matrix[:, x_index].astype(np.float64)
        y = self._matrix[:, y_index].astype(np.float64)
        if kind == "box":
            return (
                (x >= selection["x_min"])
                & (x <= selection["x_max"])
                & (y >= selection["y_min"])
                & (y <= selection["y_max"])
            )

        vertices = np.asarray(selection.get("vertices", []), dtype=np.float64)
        if vertices.ndim != 2 or vertices.shape[0] < 3 or vertices.shape[1] != 2:
            return mask
        x_min, y_min = vertices.min(axis=0)
        x_max, y_max = vertices.max(axis=0)
        candidates = np.flatnonzero((x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max))
        px = x[candidates]
        py = y[candidates]
        inside = np.zeros(candidates.size, dtype=bool)
        previous = vertices[-1]
        for current in vertices:
            x1, y1 = previous
            x2, y2 = current
            if y2 != y1:
                crosses = (y1 > py) != (y2 > py)
                edge_x = (x2 - x1) * (py - y1) / (y2 - y1) + x1
                inside ^= crosses & (px < edge_x)
            previous = current
        mask[candidates] = inside
        return mask

    def keep(self) -> None:
        """Keep only the rows inside the current selection (a no-op without one)."""
        self._add_filter("keep")

    def exclude(self) -> None:
        """Drop the rows inside the current selection (a no-op without one)."""
        self._add_filter("exclude")

    def reset(self) -> None:
        """Remove every Keep/Exclude filter and clear the selection."""
        self.filters = []
        self.clear_selection()

    def _add_filter(self, action: str) -> None:
        if self.selection.get("type") not in ("box", "lasso"):
            return
        self.filters = [*self.filters, {"action": action, "selection": dict(self.selection)}]
        self.clear_selection()

    def get_active_mask(self):
        """Return a boolean NumPy mask of the rows left after all filters."""
        import numpy as np

        active = np.ones(self._matrix.shape[0], dtype=bool)
        for step in self.filters:
            inside = self._selection_mask(step.get("selection", {}))
            if step.get("action") == "keep":
                active &= inside
            elif step.get("action") == "exclude":
                active &= ~inside
        return active

    def get_mask(self):
        """Return an exact boolean NumPy mask for the current selection.

        Only rows that survive the Keep/Exclude filters can be selected.
        """
        mask = self._selection_mask(self.selection)
        if self.filters and mask.any():
            mask &= self.get_active_mask()
        return mask

    def get_indices(self):
        """Return exact integer row indices inside the current selection."""
        import numpy as np

        return np.flatnonzero(self.get_mask())

    @property
    def selected_data(self):
        """Return selected rows in the same broad container type as the input."""
        return self._take(self.get_indices())

    @property
    def active_data(self):
        """Return the rows left after Keep/Exclude filters, like the input type."""
        import numpy as np

        return self._take(np.flatnonzero(self.get_active_mask()))

    def _take(self, indices):
        if self._source_kind == "pandas":
            return self._source_data.iloc[indices]
        if self._source_kind == "polars":
            return self._source_data[indices.tolist()]
        return self._source_data[indices]

    @traitlets.observe("selection", "filters")
    def _update_selected_count(self, change: dict[str, Any]) -> None:
        if hasattr(self, "_matrix"):
            self.selected_count = int(self.get_mask().sum())

    def _handle_frontend_message(
        self, _widget: Any, content: dict[str, Any], _buffers: list[memoryview]
    ) -> None:
        if content.get("type") == "ready":
            self._send_data()

    def _send_data(self) -> None:
        if not hasattr(self, "_matrix"):
            return
        self.send(
            {
                "type": "pair-plot-data",
                "rows": int(self._matrix.shape[0]),
                "columns": int(self._matrix.shape[1]),
                "version": int(self.data_version),
            },
            buffers=[
                memoryview(self._matrix).cast("B"),
                memoryview(self._color_codes).cast("B"),
            ],
        )


def _normalize_input(
    data: Any,
    *,
    columns: Sequence[str] | None,
    color: Any,
):
    import numpy as np

    source_kind = "numpy"
    frame_columns = None
    if hasattr(data, "columns") and hasattr(data, "to_numpy"):
        module = type(data).__module__.split(".", 1)[0]
        source_kind = "polars" if module == "polars" else "pandas"
        frame_columns = [str(value) for value in data.columns]

    color_values = color
    if isinstance(color, str):
        if frame_columns is None:
            raise TypeError("A string `color` value requires a DataFrame input.")
        if color not in frame_columns:
            raise ValueError(f"Unknown color column: {color!r}.")
        color_values = data[color]

    if frame_columns is not None:
        if columns is None:
            selected_columns = [
                name
                for name in frame_columns
                if name != color and np.asarray(data[name]).dtype.kind in "biuf"
            ]
        else:
            selected_columns = [str(name) for name in columns]
            missing = [name for name in selected_columns if name not in frame_columns]
            if missing:
                raise ValueError(f"Unknown data columns: {missing!r}.")
        values = data[selected_columns].to_numpy()
        names = selected_columns
    else:
        values = data
        array = np.asarray(values)
        if array.ndim != 2:
            raise ValueError("`data` must be a two-dimensional numeric array.")
        if columns is None:
            names = [f"x{i}" for i in range(array.shape[1])]
        else:
            names = [str(name) for name in columns]
            if len(names) != array.shape[1]:
                raise ValueError("`columns` must contain one label per array column.")

    try:
        matrix = np.ascontiguousarray(values, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise TypeError("PairPlot data columns must all be numeric.") from exc
    if matrix.ndim != 2:
        raise ValueError("`data` must be a two-dimensional numeric array.")
    if matrix.shape[1] < 2:
        raise ValueError("PairPlot needs at least two numeric dimensions.")
    if matrix.shape[0] == 0:
        raise ValueError("PairPlot needs at least one data row.")

    color_array = None
    if color_values is not None:
        if hasattr(color_values, "to_numpy"):
            color_values = color_values.to_numpy()
        color_array = np.asarray(color_values).reshape(-1)
        if color_array.shape[0] != matrix.shape[0]:
            raise ValueError("`color` must contain one value per data row.")
    return matrix, names, color_array, source_kind


def _encode_colors(values: Any, color_map: Mapping[Any, str] | None, n_rows: int):
    """Map category values to int32 codes, in sorted category order."""
    import numpy as np

    if values is None:
        return np.zeros(n_rows, dtype=np.int32), [], [_DEFAULT_COLORS[0]]

    try:
        uniques, inverse = np.unique(values, return_inverse=True)
    except TypeError:
        # Mixed, unorderable values (e.g. None next to strings): compare as text.
        uniques, inverse = np.unique(values.astype(str), return_inverse=True)
    codes = np.ascontiguousarray(inverse.reshape(-1), dtype=np.int32)

    raw_categories = [value.item() if hasattr(value, "item") else value for value in uniques]
    labels = [str(value) for value in raw_categories]
    palette = [
        _mapped_color(color_map, value) or _palette_color(index)
        for index, value in enumerate(raw_categories)
    ]
    return codes, labels, palette


def _mapped_color(color_map: Mapping[Any, str] | None, value: Any) -> str | None:
    if color_map is None:
        return None
    try:
        result = color_map.get(value)
    except TypeError:
        result = color_map.get(str(value))
    if result is None:
        result = color_map.get(str(value))
    return str(result) if result is not None else None


def _palette_color(index: int) -> str:
    if index < len(_DEFAULT_COLORS):
        return _DEFAULT_COLORS[index]
    hue = (index * 0.618033988749895) % 1.0
    red, green, blue = colorsys.hls_to_rgb(hue, 0.52, 0.58)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"
