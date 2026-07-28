---
title: "ModuleTreeWidget: PyTorch nn.Module viewer"
description: ModuleTreeWidget shows a PyTorch nn.Module as an expandable tree of parameter counts, shapes and trainable or frozen badges, for use in Jupyter.
image: moduletree
image_alt: ModuleTreeWidget showing a PyTorch model tree with per-layer parameter counts, shapes and trainable badges
---

# ModuleTreeWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<div class="wiggly-demo wiggly-demo--static">
<img class="wiggly-demo__poster" src="../assets/gallery/moduletree.webp" alt="ModuleTreeWidget showing a PyTorch model tree with per-layer parameter counts, shapes and trainable badges" decoding="async">
</div>
</div>
<!-- /no-md -->

`ModuleTreeWidget` turns a PyTorch `nn.Module` into an expandable tree: every submodule with
its parameter count and per-tensor shapes, plus trainable, frozen and buffer badges and a
density indicator, so you can see where the weights in a model actually sit. If you work in
marimo you do not need it — returning an `nn.Module` from a cell renders the same view, since
this widget has graduated to marimo core — but it still works in plain Jupyter and other
anywidget hosts.

PyTorch is too heavy to run in the browser, so this page has no in-browser demo —
[run it on molab](https://molab.marimo.io/notebooks/nb_K7QvvoASZErgKxwD8XSMWi?utm_source=wigglystuff)
instead. See also: [NestedTable](nested-table.md) for the same collapsing-tree layout over
any hierarchy, [Treemap](treemap.md) for sizing a hierarchy by value, and
[LiveEdit](live-edit.md) for tracing what a Python function does line by line.

::: wigglystuff.module_tree.ModuleTreeWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `tree` | `dict` | JSON-serializable tree extracted from a PyTorch `nn.Module`. |
| `initial_expand_depth` | `int` | Number of tree levels to expand on first render (default: 1). |
