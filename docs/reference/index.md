---
title: "API reference: every wigglystuff widget"
description: Reference index for all wigglystuff AnyWidgets, grouped by what they do — sliders, curves, charts, graphs, drawing surfaces, device input and tracing.
---

# API Overview

Every widget in `wigglystuff` has its own reference page below, grouped by what it is
for. Each page is generated with mkdocstrings, so docstrings and trait metadata stay in
sync with the source on every release — and each one carries a live demo you can run in
the browser.

Every page is also available as raw Markdown: swap the trailing `/` for `.md`, or use
the link at the top of any page. [`llms.txt`](../llms.txt) lists them all.

## Sliders and scalar inputs

- [Slider2D](slider2d.md) — 2D pointer for two coupled parameters
- [CircularSlider](circular-slider.md) — circular dial for a single value or a span
- [HoverSlider](hover-slider.md) — reports the committed value and the live hover value
- [PlaySlider](play-slider.md) — slider with a play/pause button that auto-advances
- [Tangle widgets](tangle.md) — inline draggable numbers, toggles and dropdowns
- [TangleLatex](tangle-latex.md) — LaTeX formula with draggable numbers and symbols
- [Matrix](matrix.md) — spreadsheet-like numeric matrix editor
- [SortableList](sortable-list.md) — drag-and-drop ordering with optional CRUD
- [ColorPicker](color-picker.md) — native color input with an `rgb` helper

## Curves

- [BezierCurve](bezier-curve.md) — arbitrary-degree Bezier editor with playback
- [CurveEditor](curve-editor.md) — chart-space curves via D3 line interpolators
- [SplineDraw](spline-draw.md) — draw points, fit the spline in Python

## Charts and plots

- [AltairWidget](altair-widget.md) — flicker-free Altair chart with smooth data updates
- [ScatterLog](scatter-log.md) — accumulate reactive values into a live scatter plot
- [ObservablePlot](observable-plot.md) — run Observable Plot JS with Python variables
- [RidgelineChart](ridgeline-chart.md) — stacked "Joy Division" waveforms, clickable rows
- [ParallelCoordinates](parallel-coords.md) — HiPlot parallel coordinates with brushing

## Selecting on top of charts

- [ChartPuck](chart-puck.md) — draggable puck over a matplotlib chart
- [ChartSelect](chart-select.md) — box and lasso selection on a matplotlib chart
- [ChartMultiSelect](chart-multi-select.md) — multi-region class-labeled selection
- [ScatterWidget](scatter-widget.md) — paint multi-class 2D scatter data with a brush

## Hierarchies and tables

- [Treemap](treemap.md) — zoomable hierarchical treemap with breadcrumbs
- [NestedTable](nested-table.md) — table with expandable nested rows
- [ModuleTreeWidget](module-tree.md) — tree viewer for a PyTorch `nn.Module`

## Graphs and diagrams

- [GraphWidget](graph-widget.md) — programmatic force-directed graph
- [EdgeDraw](edge-draw.md) — sketch node/link diagrams and query adjacency
- [WidgetDAG](widget-dag.md) — arrange live widgets as a DAG and draw the arrows
- [Neo4jWidget](neo4j-widget.md) — Neo4j graph explorer with a Cypher query box

## Drawing surfaces

- [Paint](paint.md) — MS-Paint-style canvas with PIL helpers
- [Excalidraw](excalidraw.md) — embedded Excalidraw whiteboard
- [GridDraw](grid-draw.md) — dots on grid intersections, orthogonal segments between

## 3D

- [ThreeWidget](three-widget.md) — 3D scatter plot for point clouds
- [CubeWidget](cube-widget.md) — rotatable 3D cube

## Device and browser input

- [GamepadWidget](gamepad.md) — streams browser Gamepad API events
- [KeystrokeWidget](keystroke.md) — captures the latest keypress with modifiers
- [WebkitSpeechToTextWidget](talk.md) — WebKit speech recognition bridge
- [WebcamCapture](webcam-capture.md) — webcam preview with snapshot capture
- [AnnotationWidget](annotation.md) — buttons, keyboard, gamepad and speech in one

## Live output and tracing

- [ImageRefreshWidget](image-refresh.md) — swap an image in place without re-rendering
- [HTMLRefreshWidget](html-refresh.md) — swap HTML in place without re-rendering
- [ProgressBar](progress-bar.md) — progress bar you can drive from a loop
- [FramePlayer](frame-player.md) — play a sequence of images as an inline video
- [AsyncFlow](async-flow.md) — swimlane timeline of one async run (Python 3.12+)
- [LiveEdit](live-edit.md) — source-linked loop trace for one function run
- [CellTour](cell-tour.md) — cell-based guided tours for marimo
- [Hint](hint.md) — curve an arrow from a note to the widget it explains

## Images

- [HoverZoom](hover-zoom.md) — image hover zoom with a magnified side panel

## Escape hatches and utilities

- [EsmWidget](esm-widget.md) — inline ES module from any CDN with a two-way data bridge
- [ManimWeb](manim-web.md) — run a browser-Manim scene from JS, a file, or a URL
- [ApiDoc](api-doc.md) — render API docs for Python classes and functions
- [EnvConfig](env-config.md) — environment variable config with validation
- [TextCompare](text-compare.md) — side-by-side text diff with match highlighting
- [CopyToClipboard](copy-to-clipboard.md) — copy a payload to the OS clipboard
- [Utils](utils.md) — `altair2svg`, `forecast_chart` and the refresh helpers
