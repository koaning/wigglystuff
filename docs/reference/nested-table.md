---
title: "NestedTable: expandable hierarchy table"
description: NestedTable renders a hierarchy as an expandable table with one column per value key and optional share-of-root percentages, in marimo or Colab.
image: nested_table
image_alt: NestedTable showing an expandable project hierarchy with hours and percentage columns
---

# NestedTable API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="nested_table" data-demo-title="NestedTable live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/nested_table.webp" alt="NestedTable showing an expandable project hierarchy with hours and percentage columns" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`NestedTable` shows a hierarchy as a table of collapsible rows: the node name, one column per
value key (or a single `Value` column for scalar trees), and an optional share-of-root
percentage beside any subset of those columns. Use it when the numbers themselves matter and
a chart would only approximate them — cost breakdowns, test timings, rolled-up group totals.
It reads the same tree format as `Treemap` and shares its `from_paths`, `from_records` and
`from_dataframe` constructors, while `expanded_paths` and `selected_path` sync both ways.

See also: [Treemap](treemap.md) for the same hierarchy drawn as nested rectangles,
[ModuleTreeWidget](module-tree.md) for a tree of PyTorch layers, and
[Matrix](matrix.md) for editing a flat grid of numbers instead.

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
