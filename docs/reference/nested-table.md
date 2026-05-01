# NestedTable API

::: wigglystuff.nested_table.NestedTable

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
