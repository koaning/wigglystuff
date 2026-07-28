---
title: "ApiDoc: render Python API docs inline"
description: ApiDoc introspects a Python class or function and renders its signature, parameters, docstring and methods as a formatted card inside a Jupyter notebook.
image: apidoc
image_alt: ApiDoc widget showing a function signature, a parameter table with types and the docstring
---

# ApiDoc API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="apidoc" data-demo-title="ApiDoc live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/apidoc.webp" alt="ApiDoc widget showing a function signature, a parameter table with types and the docstring" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ApiDoc` takes a Python class or function and renders what `inspect` can see about it —
the signature, a parameter table with types and defaults, the docstring, and any methods
and properties — as a formatted card in the notebook, without a docs build in the loop.
Useful when you are teaching a library in a notebook and want the reference sitting next
to the example instead of in another tab; `show_private` decides whether
underscore-prefixed methods show up.

See also: [ModuleTreeWidget](module-tree.md) for inspecting a PyTorch module's structure,
[LiveEdit](live-edit.md) for showing what a function actually does when it runs, and
[CellTour](cell-tour.md) for walking a reader through the notebook around it.

::: wigglystuff.api_doc.ApiDoc

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `doc` | `dict` | Introspected documentation payload (auto-generated from the target object). |
| `width` | `int` | Container width in pixels. |
| `show_private` | `bool` | Whether to include private (underscore-prefixed) methods. |
