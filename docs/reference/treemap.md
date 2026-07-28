---
title: "Treemap: zoomable treemap with breadcrumbs"
description: Treemap draws a hierarchy as nested rectangles you zoom into by clicking, with a breadcrumb bar to zoom back out and the clicked path synced to Python.
image: treemap
image_alt: Treemap showing nested colored rectangles sized by test duration and grouped by module
---

# Treemap API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="treemap" data-demo-title="Treemap live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/treemap.webp" alt="Treemap showing nested colored rectangles sized by test duration and grouped by module" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`Treemap` draws a `{name, value, children}` hierarchy as nested rectangles: click one to zoom
into its subtree, click the breadcrumb bar above the chart to zoom back out. Leaf values can
be a single number or a `{column: number}` dict, in which case `value_col` picks the column
that sizes the rectangles. You rarely build the tree by hand — `from_paths`, `from_records`
and `from_dataframe` cover slash-separated paths, record dicts and pandas or polars frames —
and `selected_path` plus `clicked_path` report where the reader is looking.

See also: [NestedTable](nested-table.md) for the same tree shown as an expandable table,
[ModuleTreeWidget](module-tree.md) for the PyTorch-specific version of that idea, and
[GraphWidget](graph-widget.md) for hierarchies that are really graphs.

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
