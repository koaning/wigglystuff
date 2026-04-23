# Treemap API

::: wigglystuff.treemap.Treemap

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `dict` | Hierarchy `{name, value?, children?}`. Leaf `value` is a number or `{column: number}`. |
| `width` | `int \| str` | Chart width in pixels, or a CSS length like `"100%"`. |
| `height` | `int` | Chart height in pixels. |
| `max_depth` | `int` | How many levels below the current zoom to draw. |
| `value_col` | `str` | When leaves carry dicts, the column that drives rectangle sizing. |
| `selected_path` | `list[str]` | Breadcrumb path of the currently-zoomed node. |
| `clicked_path` | `list[str]` | Path of the most recently clicked node (fires for leaves too). |

## Alternate constructors

- `Treemap.from_paths(mapping, sep="/", root_name="root")` — build from `{path_string: value}`.
- `Treemap.from_records(records, path_cols, value_cols=None, root_name="root")` — build from a list of record dicts. `value_cols` accepts `str`, a list of names (controlling column order), or `None` to auto-detect every numeric field.
- `Treemap.from_dataframe(df, path_cols, value_cols=None, root_name="root")` — build from a pandas or polars dataframe. Same `value_cols` semantics.
