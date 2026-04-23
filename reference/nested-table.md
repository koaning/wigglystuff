# NestedTable API


 Bases: `AnyWidget`


Recursive expandable table for hierarchical data.


Each row shows the node name followed by one column per value key (or a single `Value` column when values are scalars), and optionally a share-of-root column next to any subset of value columns.




```
from wigglystuff import NestedTable

from wigglystuff import NestedTable

widget = NestedTable.from_paths(
    {
        "analytics/cluster/Agg": {"hours": 12.5, "count": 5},
        "analytics/graph/Shortest": {"hours": 6.0, "count": 2},
        "animate/Easing": {"hours": 4.25, "count": 8},
    },
    format={"hours": lambda v: f"{v:.1f}h"},
    show_percent=["hours"],
)
widget
```

 Source code in `wigglystuff/nested_table.py`

```
def __init__(
    self,
    data: Mapping[str, Any] | None = None,
    *,
    initial_expand_depth: int = 1,
    show_percent: bool | Sequence[str] = True,
    format: Formatter | Mapping[str, Formatter] | None = None,
    width: str = "100%",
):
    prepared, cols = self._prepare(data, formatter=format)
    effective_cols = cols or ["value"]
    if show_percent is True:
        pct_cols = list(effective_cols)
    elif show_percent is False:
        pct_cols = []
    else:
        pct_cols = [c for c in show_percent if c in effective_cols]
        missing = [c for c in show_percent if c not in effective_cols]
        if missing:
            raise ValueError(
                f"show_percent columns {missing} not found; "
                f"available: {effective_cols}"
            )
    super().__init__(
        data=prepared,
        columns=cols,
        show_percent=pct_cols,
        initial_expand_depth=initial_expand_depth,
        width=width,
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
) -> "NestedTable"
```


Build a `NestedTable` from a pandas or polars dataframe.



```
from wigglystuff import NestedTable

import pandas as pd
from wigglystuff import NestedTable

df = pd.DataFrame(
    {
        "team": ["analytics", "analytics", "animate"],
        "project": ["cluster", "graph", "easing"],
        "hours": [12.5, 6.0, 4.25],
        "count": [5, 2, 8],
    }
)
NestedTable.from_dataframe(
    df,
    path_cols=["team", "project"],
    value_cols=["hours", "count"],
)
```

 Source code in `wigglystuff/nested_table.py`

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
) -> "NestedTable":
    """Build a ``NestedTable`` from a pandas or polars dataframe.

    Examples:
        ```python
        import pandas as pd
        from wigglystuff import NestedTable

        df = pd.DataFrame(
            {
                "team": ["analytics", "analytics", "animate"],
                "project": ["cluster", "graph", "easing"],
                "hours": [12.5, 6.0, 4.25],
                "count": [5, 2, 8],
            }
        )
        NestedTable.from_dataframe(
            df,
            path_cols=["team", "project"],
            value_cols=["hours", "count"],
        )
        ```
    """
    tree = tree_from_dataframe(
        df, path_cols=path_cols, value_cols=value_cols, root_name=root_name
    )
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
) -> "NestedTable"
```


Build a `NestedTable` from a mapping of path strings to leaf values.



```
from wigglystuff import NestedTable

from wigglystuff import NestedTable

NestedTable.from_paths(
    {
        "analytics/cluster/Agg": {"hours": 12.5, "count": 5},
        "analytics/graph/Shortest": {"hours": 6.0, "count": 2},
        "animate/Easing": {"hours": 4.25, "count": 8},
    },
    show_percent=["hours"],
)
```

 Source code in `wigglystuff/nested_table.py`

```
@classmethod
def from_paths(
    cls,
    mapping: Mapping[str, Any],
    *,
    sep: str = "/",
    root_name: str = "root",
    **kwargs: Any,
) -> "NestedTable":
    """Build a ``NestedTable`` from a mapping of path strings to leaf values.

    Examples:
        ```python
        from wigglystuff import NestedTable

        NestedTable.from_paths(
            {
                "analytics/cluster/Agg": {"hours": 12.5, "count": 5},
                "analytics/graph/Shortest": {"hours": 6.0, "count": 2},
                "animate/Easing": {"hours": 4.25, "count": 8},
            },
            show_percent=["hours"],
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
) -> "NestedTable"
```


Build a `NestedTable` from an iterable of record dicts.



```
from wigglystuff import NestedTable

from wigglystuff import NestedTable

NestedTable.from_records(
    [
        {"team": "analytics", "project": "cluster", "hours": 12.5},
        {"team": "analytics", "project": "graph", "hours": 6.0},
        {"team": "animate", "project": "easing", "hours": 4.25},
    ],
    path_cols=["team", "project"],
    value_cols="hours",
)
```

 Source code in `wigglystuff/nested_table.py`

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
) -> "NestedTable":
    """Build a ``NestedTable`` from an iterable of record dicts.

    Examples:
        ```python
        from wigglystuff import NestedTable

        NestedTable.from_records(
            [
                {"team": "analytics", "project": "cluster", "hours": 12.5},
                {"team": "analytics", "project": "graph", "hours": 6.0},
                {"team": "animate", "project": "easing", "hours": 4.25},
            ],
            path_cols=["team", "project"],
            value_cols="hours",
        )
        ```
    """
    tree = tree_from_records(
        records, path_cols=path_cols, value_cols=value_cols, root_name=root_name
    )
    return cls(tree, **kwargs)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `dict` | Hierarchy `{name, value?, children?}`. Leaf `value` is a number or `{column: number}`. |
| `columns` | `list[str]` | Auto-detected dict-value column keys. Empty for scalar trees. |
| `show_percent` | `list[str]` | Column names that show a share-of-root column. Constructor accepts `bool` or `Sequence[str]` and normalizes. |
| `initial_expand_depth` | `int` | How many levels are expanded on first render. |
| `expanded_paths` | `list[list[str]]` | Paths of currently-expanded rows. Bidirectional. |
| `selected_path` | `list[str]` | Path of the last row whose name was clicked. Selection is highlighted in the UI. |
| `width` | `str` | CSS width of the table. |


## Alternate constructors



- `NestedTable.from_paths(mapping, sep="/", root_name="root")` — build from `{path_string: value}`.

- `NestedTable.from_records(records, path_cols, value_cols=None, root_name="root")` — build from a list of record dicts. `value_cols` accepts `str`, a list of names (controlling column order), or `None` to auto-detect every numeric field.

- `NestedTable.from_dataframe(df, path_cols, value_cols=None, root_name="root")` — build from a pandas or polars dataframe. Same `value_cols` semantics.
