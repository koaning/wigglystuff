---
title: "ScatterWidget: paint labeled scatter data"
description: ScatterWidget is a brush-based canvas for painting labeled multi-class 2D scatter data, letting you invent a small toy dataset by hand in Colab or Jupyter.
image: scatterwidget
image_alt: ScatterWidget widget showing two moons painted in blue and a round orange cluster, with class buttons and a brush-size slider
---

# ScatterWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="scatterwidget" data-demo-title="ScatterWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/scatterwidget.webp" alt="ScatterWidget widget showing two moons painted in blue and a round orange cluster, with class buttons and a brush-size slider" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ScatterWidget` is a paintable scatter canvas: pick a class color, drag the brush, and the
points you paint come back as `data` (or as a DataFrame via `data_as_pandas`). It is the
fastest way to invent a small labeled 2D dataset for testing a classifier, sanity-checking
a clustering algorithm, or drawing the pathological case you want to explain. Up to four
classes, each with its own color and label, plus a `batch` key per stroke.

See also: [SplineDraw](spline-draw.md) for the same canvas with a Python-fitted curve on
top, [ChartMultiSelect](chart-multi-select.md) for labeling data you already have, and
[ScatterLog](scatter-log.md) for accumulating computed points rather than drawn ones.

> **Note:** `ScatterWidget` is provided by the [`drawdata`](https://github.com/koaning/drawdata) package and re-exported here for convenience. You can use it via `from wigglystuff import ScatterWidget` or `from drawdata import ScatterWidget`.

::: wigglystuff.scatter_widget.ScatterWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | List of drawn points with `x`, `y`, `color`, `label`, `batch` keys. |
| `brushsize` | `int` | Brush radius in pixels (default: 40). |
| `width` | `int` | SVG viewBox width in pixels (default: 800). |
| `height` | `int` | SVG viewBox height in pixels (default: 400). |
| `n_classes` | `int` | Number of point classes, 1-4 (default: 4). |
