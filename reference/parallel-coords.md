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


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | Input rows rendered as polylines. |
| `color_by` | `str` | Column used for line coloring. |
| `color_map` | `dict` | Map of categorical values to CSS colors (e.g. `{"a": "red", "b": "#00f"}`). Unmapped values use the default palette. |
| `height` | `int` | Plot height in pixels. |
| `width` | `int` | Plot width in pixels. Set to 0 for container width. |
| `filtered_indices` | `list[int]` | Indices currently passing filters/selection. |
| `selected_indices` | `list[int]` | Indices currently selected in the active brush. |
