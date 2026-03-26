# ParallelCoordinates API


 Bases: `AnyWidget`


Interactive parallel coordinates plot powered by HiPlot.


Wraps Facebook Research's HiPlot library to provide brush filtering on axes, axis reordering via drag, and coloring lines by a selected dimension -- all inside a notebook widget.




```
from wigglystuff import ParallelCoordinates

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


Create a ParallelCoordinates widget.


  Source code in `wigglystuff/parallel_coords.py`

```
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
```


## filtered_as_pandas `property`


```
filtered_as_pandas
```


Return filtered data as a :class:`pandas.DataFrame`.


## filtered_as_polars `property`


```
filtered_as_polars
```


Return filtered data as a :class:`polars.DataFrame`.


## filtered_data `property`


```
filtered_data: list[dict]
```


Return the subset of data rows passing all brush filters.


## selected_data `property`


```
selected_data: list[dict]
```


Return the subset of data rows that are selected.


## selections `property`


```
selections: list[dict]
```


Return the full filtering state including the active brush.


Returns a list of `{"action": ..., "extents": ...}` dicts. Completed Keep/Exclude steps come first, followed by a `{"action": "current", "extents": ...}` entry if there is an active brush on any axis.


## exclude


```
exclude() -> None
```


Trigger an Exclude action on the current brush selection.


Equivalent to clicking the Exclude button in the UI. Rows inside the current brush are removed. The action and brush extents are recorded in :attr:`filter_history`.

 Source code in `wigglystuff/parallel_coords.py`

```
def exclude(self) -> None:
    """Trigger an Exclude action on the current brush selection.

    Equivalent to clicking the Exclude button in the UI. Rows inside
    the current brush are removed. The action and brush extents are
    recorded in :attr:`filter_history`.
    """
    self._action_request = {"action": "exclude", "ts": _ts()}
```


## keep


```
keep() -> None
```


Trigger a Keep action on the current brush selection.


Equivalent to clicking the Keep button in the UI. Rows outside the current brush are removed. The action and brush extents are recorded in :attr:`filter_history`.

 Source code in `wigglystuff/parallel_coords.py`

```
def keep(self) -> None:
    """Trigger a Keep action on the current brush selection.

    Equivalent to clicking the Keep button in the UI. Rows outside
    the current brush are removed. The action and brush extents are
    recorded in :attr:`filter_history`.
    """
    self._action_request = {"action": "keep", "ts": _ts()}
```


## restore


```
restore() -> None
```


Restore all rows and clear the filter history.


Equivalent to clicking the Restore button in the UI. All Keep/Exclude operations are undone and :attr:`filter_history` is reset to an empty list.

 Source code in `wigglystuff/parallel_coords.py`

```
def restore(self) -> None:
    """Restore all rows and clear the filter history.

    Equivalent to clicking the Restore button in the UI. All
    Keep/Exclude operations are undone and :attr:`filter_history`
    is reset to an empty list.
    """
    self._action_request = {"action": "restore", "ts": _ts()}
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | Input rows rendered as polylines. |
| `color_by` | `str` | Column used for line coloring. |
| `color_map` | `dict` | Map of categorical values to CSS colors (e.g. `{"a": "red", "b": "#00f"}`). Unmapped values use the default palette. |
| `height` | `int` | Plot height in pixels. |
| `width` | `int` | Plot width in pixels. Set to 0 for container width. |
| `brush_extents` | `dict` | Current brush ranges on axes. Resets to `{}` after Keep/Exclude. |
| `filtered_indices` | `list[int]` | Indices currently passing filters/selection. |
| `selected_indices` | `list[int]` | Indices currently selected in the active brush. |


## Methods


| Method | Description |
| --- | --- |
| `selections` | Property returning `filter_history` + a trailing `{"action": "current", "extents": ...}` entry for the active brush (if any). |
| `keep()` | Trigger a Keep action on the current brush selection (same as the Keep button). |
| `exclude()` | Trigger an Exclude action on the current brush selection (same as the Exclude button). |
| `restore()` | Restore all rows and clear `filter_history` (same as the Restore button). |
| `filtered_data` | Property returning the list of dicts for rows passing all filters. |
| `filtered_as_pandas` | Property returning filtered data as a pandas DataFrame. |
| `filtered_as_polars` | Property returning filtered data as a polars DataFrame. |
| `selected_data` | Property returning the list of dicts for selected rows. |
