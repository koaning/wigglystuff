---
title: "HTMLRefreshWidget: refresh HTML in a cell"
description: HTMLRefreshWidget rewrites a div's contents whenever its html traitlet changes, so SVG charts or status text update in place inside a marimo notebook.
image: htmlwidget
image_alt: HTMLRefreshWidget displaying the text Counting 9, rewritten in place by a loop in the cell below it
---

# HTMLRefreshWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="htmlwidget" data-demo-title="HTMLRefreshWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/htmlwidget.webp" alt="HTMLRefreshWidget displaying the text Counting 9, rewritten in place by a loop in the cell below it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`HTMLRefreshWidget` keeps one `div` around and rewrites its contents every time the `html`
traitlet changes. It is the escape hatch for anything you can already express as markup —
an SVG chart, a small table, a line of status text — updated in place from a running cell
instead of printed again underneath. Note that the value is inserted as HTML, so only pass
markup you trust.

See also: [ImageRefreshWidget](image-refresh.md) for the same pattern with a rasterised
image, [ProgressBar](progress-bar.md) for the common case of showing a percentage, and
[EsmWidget](esm-widget.md) for when the thing you want to refresh needs JavaScript.

::: wigglystuff.html.HTMLRefreshWidget

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `html` | `str` | The HTML content to display. |
