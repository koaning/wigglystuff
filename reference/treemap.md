# Treemap API


 Bases: `AnyWidget`


Zoomable hierarchical treemap.


Click a rectangle to zoom into its subtree; click the breadcrumb bar above the chart to zoom back out. Parent rectangles reserve a header strip for their name and aggregated value; children render nested inside, up to `max_depth` levels below the current view.


Values on each leaf can be a single number, or a dict of `{column: number}` for multi-column data. In the multi-column case, pass `value_col` to pick which column drives rectangle sizing.




```
from wigglystuff import Treemap

from wigglystuff import Treemap

Treemap.from_paths(
    {
        "analytics/cluster/Agg": {"hours": 10, "count": 5},
        "analytics/graph/Shortest": {"hours": 6, "count": 2},
        "animate/Easing": {"hours": 4, "count": 8},
    },
    value_col="hours",
)
```

 Source code in `wigglystuff/treemap.py`

```
def __init__(
    self,
    data: Mapping[str, Any] | None = None,
    *,
    width: int | str = 600,
    height: int = 400,
    max_depth: int = 3,
    value_col: str | None = None,
    format: Callable[[float], str] | None = None,
):
    prepared = self._prepare(data, value_col=value_col, formatter=format)
    super().__init__(
        data=prepared,
        width=width,
        height=height,
        max_depth=max_depth,
        value_col=value_col or "",
    )
```


## from_dataframe `classmethod`


```
from_dataframe(
    df: Any,
    *,
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None = None,
    root_name: str = "root",
    **kwargs: Any
) -> "Treemap"
```


Build a `Treemap` from a pandas or polars dataframe.



```
from wigglystuff import Treemap

import pandas as pd
from wigglystuff import Treemap

df = pd.DataFrame(
    {
        "team": ["analytics", "analytics", "animate"],
        "project": ["cluster", "graph", "easing"],
        "hours": [10, 6, 4],
    }
)
Treemap.from_dataframe(
    df,
    path_cols=["team", "project"],
    value_cols="hours",
)
```

 Source code in `wigglystuff/treemap.py`

```
@classmethod
def from_dataframe(
    cls,
    df: Any,
    *,
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None = None,
    root_name: str = "root",
    **kwargs: Any,
) -> "Treemap":
    """Build a ``Treemap`` from a pandas or polars dataframe.

    Examples:
        ```python
        import pandas as pd
        from wigglystuff import Treemap

        df = pd.DataFrame(
            {
                "team": ["analytics", "analytics", "animate"],
                "project": ["cluster", "graph", "easing"],
                "hours": [10, 6, 4],
            }
        )
        Treemap.from_dataframe(
            df,
            path_cols=["team", "project"],
            value_cols="hours",
        )
        ```
    """
    tree = tree_from_dataframe(
        df, path_cols=path_cols, value_cols=value_cols, root_name=root_name
    )
    cls._auto_pick_value_col(tree, value_cols, kwargs)
    return cls(tree, **kwargs)
```


## from_paths `classmethod`


```
from_paths(
    mapping: Mapping[str, Any],
    *,
    sep: str = "/",
    root_name: str = "root",
    **kwargs: Any
) -> "Treemap"
```


Build a `Treemap` from a mapping of path strings to leaf values.



```
from wigglystuff import Treemap

from wigglystuff import Treemap

Treemap.from_paths(
    {
        "analytics/cluster/Agg": {"hours": 10, "count": 5},
        "analytics/graph/Shortest": {"hours": 6, "count": 2},
        "animate/Easing": {"hours": 4, "count": 8},
    },
    value_col="hours",
)
```

 Source code in `wigglystuff/treemap.py`

```
@classmethod
def from_paths(
    cls,
    mapping: Mapping[str, Any],
    *,
    sep: str = "/",
    root_name: str = "root",
    **kwargs: Any,
) -> "Treemap":
    """Build a ``Treemap`` from a mapping of path strings to leaf values.

    Examples:
        ```python
        from wigglystuff import Treemap

        Treemap.from_paths(
            {
                "analytics/cluster/Agg": {"hours": 10, "count": 5},
                "analytics/graph/Shortest": {"hours": 6, "count": 2},
                "animate/Easing": {"hours": 4, "count": 8},
            },
            value_col="hours",
        )
        ```
    """
    return cls(tree_from_paths(mapping, sep=sep, root_name=root_name), **kwargs)
```


## from_records `classmethod`


```
from_records(
    records: Iterable[Mapping[str, Any]],
    *,
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None = None,
    root_name: str = "root",
    **kwargs: Any
) -> "Treemap"
```


Build a `Treemap` from an iterable of record dicts.



```
from wigglystuff import Treemap

from wigglystuff import Treemap

Treemap.from_records(
    [
        {"team": "analytics", "project": "cluster", "hours": 10},
        {"team": "analytics", "project": "graph", "hours": 6},
        {"team": "animate", "project": "easing", "hours": 4},
    ],
    path_cols=["team", "project"],
    value_cols="hours",
)
```

 Source code in `wigglystuff/treemap.py`

```
@classmethod
def from_records(
    cls,
    records: Iterable[Mapping[str, Any]],
    *,
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None = None,
    root_name: str = "root",
    **kwargs: Any,
) -> "Treemap":
    """Build a ``Treemap`` from an iterable of record dicts.

    Examples:
        ```python
        from wigglystuff import Treemap

        Treemap.from_records(
            [
                {"team": "analytics", "project": "cluster", "hours": 10},
                {"team": "analytics", "project": "graph", "hours": 6},
                {"team": "animate", "project": "easing", "hours": 4},
            ],
            path_cols=["team", "project"],
            value_cols="hours",
        )
        ```
    """
    tree = tree_from_records(
        records, path_cols=path_cols, value_cols=value_cols, root_name=root_name
    )
    cls._auto_pick_value_col(tree, value_cols, kwargs)
    return cls(tree, **kwargs)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `dict` | Hierarchy `{name, value?, children?}`. Leaf `value` is a number or `{column: number}`. |
| `width` | `int \\| str` | Chart width in pixels, or a CSS length like `"100%"`. |
| `height` | `int` | Chart height in pixels. |
| `max_depth` | `int` | How many levels below the current zoom to draw. |
| `value_col` | `str` | When leaves carry dicts, the column that drives rectangle sizing. |
| `selected_path` | `list[str]` | Breadcrumb path of the currently-zoomed node. |
| `clicked_path` | `list[str]` | Path of the most recently clicked node (fires for leaves too). |


## Alternate constructors



- `Treemap.from_paths(mapping, sep="/", root_name="root")` — build from `{path_string: value}`.

- `Treemap.from_records(records, path_cols, value_cols=None, root_name="root")` — build from a list of record dicts. `value_cols` accepts `str`, a list of names (controlling column order), or `None` to auto-detect every numeric field.

- `Treemap.from_dataframe(df, path_cols, value_cols=None, root_name="root")` — build from a pandas or polars dataframe. Same `value_cols` semantics.
