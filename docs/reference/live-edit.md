---
title: "LiveEdit: trace a Python function run"
description: "LiveEdit renders a source-linked trace of one Python function run in marimo or Jupyter: the setup values, every loop pass, and the value returned."
image: liveedit
image_alt: LiveEdit widget showing setup values, a while-loop pass table and the returned value
---

# LiveEdit API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="liveedit" data-demo-title="LiveEdit live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/liveedit.webp" alt="LiveEdit widget showing setup values, a while-loop pass table and the returned value" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`LiveEdit` takes one call — `LiveEdit.inspect_run(fn, *args, **kwargs)` — and lays the
run out next to its source: the setup values, a row per loop pass including nested child
loops, and the value that came back. Click a numeric column header to chart that column
across passes. `LiveEdit.from_pytest("tests/test_foo.py::test_bar")` does the same for a
test body, with a failing `assert` rendered on the offending line instead of raised, so
a broken test becomes something you read rather than something you re-run with print
statements.

See also: [AsyncFlow](async-flow.md) for the same idea applied to an async run,
[ApiDoc](api-doc.md) for rendering a function's signature and docstring, and
[Matrix](matrix.md) for editing the numbers you feed in by hand.

::: wigglystuff.live_edit.LiveEdit

::: wigglystuff.live_edit.inspect_run

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Source code for the traced function. This is the future live-edit source of truth. |
| `trace` | `dict` | Structured setup values, loop passes, nested child loops, and returned value. |
| `annotations` | `dict` | Static line/token metadata used by the browser for hover linking. |
| `error` | `dict or None` | Parse, runtime, or argument mismatch error payload; `None` when the run succeeds. |
| `editable` | `bool` | Reserved for the future browser editor mode. Defaults to `False`. |
| `theme` | `str` | `"auto"`, `"light"`, or `"dark"`. |
| `width` | `int` | Widget width in pixels. |
| `height` | `int` | Maximum widget height in pixels. |
