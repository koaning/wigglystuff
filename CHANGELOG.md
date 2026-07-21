# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- New "MuJoCo Physics" example notebook (`demos/mujoco_sim.py`, linked from the docs gallery Examples section) — a headless MuJoCo simulation driven by inline `TangleSlider` controls (ball count, drop height, gravity, bounciness, clip length) that rains semi-transparent bouncing balls onto a floor, renders each step with MuJoCo's offscreen renderer, and plays the encoded `.mp4` back through `mo.video`. The gallery link boots it on a molab **server** (`…/mujoco_sim.py/server`) since MuJoCo is a native engine and can't run in WASM.

### Fixed

- `WidgetDAG` now renders each node through `mo.as_html`, so nodes that display via `_repr_html_`/`_repr_mimebundle_` (charts, raw anywidgets) show their content instead of an empty box; previously only marimo `Html`/UI nodes rendered.

### Changed

- `WidgetDAG` now raises a clear `RuntimeError` when displayed outside a running marimo notebook (in plain Jupyter/IPython or without a live kernel) instead of showing a silent plain-text repr. It renders by reaching into marimo's DOM, so it is marimo-only by design.

## [0.5.20] - 2026-07-17

### Added

- `CubeWidget`: progressively lock three configurable axes to select a plane, line, and point. The dependency-free SVG view includes smooth axis-colored sliders, reset and Python locking helpers, derived selection outputs, and light/dark theme support.
- `TangleLatex`: render a LaTeX formula with `\tangle{name}` markers whose numbers (or symbols) become draggable, Bret Victor-style tangle controls. Each parameter is configured via a `parameters` dict (bounds, step, digits, color, symbol display), the live numbers sync back through the `values` traitlet, and `reveal_all_on_drag`, `editor`, and `theme` tune the interaction. See the `demos/tangle_latex.py` demo, where the parameters drive live Observable Plot charts.

## [0.5.19] - 2026-07-16

### Added

- `WidgetDAG`: a marimo display helper that lays live widgets out as a DAG (columns by edge depth) and draws the connecting arrows for you. Pass `nodes` (id → any renderable) and `edges` (`(src_id, dst_id)` pairs); nodes stay live and reactive. `layout` is pluggable (default `layered_layout`).
- `WidgetDAG.from_widgets([...])`: skip the `edges` list — pass the widgets and the arrows are derived from marimo's dataflow graph. Needs each widget to be a top-level variable in its own cell; use `WidgetDAG(nodes, edges)` for inline or same-cell nodes.

## [0.5.18] - 2026-07-15

### Fixed

- `FramePlayer`: playback no longer stutters or flips frames out of order over a remote kernel (MoLab/sandbox). Playback and scrubbing are now fully client-side — the widget advances a local frame counter instead of round-tripping the synced `value` traitlet to the kernel on every frame, which previously created a feedback loop of out-of-order comm messages that painted stale frames. Behavior note: `value` and `playing` are now one-way Python→JS controls (setting `player.value = 10` or `player.playing = True` still drives the widget), but the widget no longer reports the live playhead or the play/pause state back to Python. Fixes #289.

## [0.5.17] - 2026-07-15

### Added

- `ObservablePlot`: run [Observable Plot](https://observablehq.com/plot/) code inline in a notebook. Plot and d3 are loaded from a CDN and your JavaScript is evaluated the way an Observable cell is — as an expression that returns a DOM node (a bare `Plot.plot({...})`), which is mounted into the widget. Python data is injected by name via the `variables` dict (e.g. `variables={"vacancies": df}` exposes `vacancies` inside the code); pandas/polars DataFrames and numpy arrays are converted to JSON records/lists automatically. `Plot`, `d3`, `container`, `width`, `height`, and `model` are always in scope. The source (`code` or `src`) can be inline JavaScript, a local `.js` file path, or an `http(s)://` URL (resolved in Python). The Plot `version` defaults to `"latest"`. JS runtime and CDN-load errors surface via the `error` traitlet.
- `Paint`: the toolbar is now configurable. New boolean flags `brush`, `marker`, `eraser`, and `color_picker` (all default `True`) hide/show individual controls, generalizing the existing `rainbow_brush` toggle — so you can build a constrained canvas like an eraser-only mask editor or a single-color annotation tool. The drawing color is now a two-way synced `color` traitlet (default `"#000000"`): it backs the picker, updates when you pick a color, and can be preset/read from Python (handy when the picker is hidden). Constructing a `Paint` with every drawing tool disabled raises `ValueError`.
- `LiveEdit.from_pytest("tests/test_foo.py::test_bar")`: point `LiveEdit` at a pytest test by node id (the same string you'd type on the command line) and trace the test body. By default pytest resolves the test's fixtures, parametrization, and `conftest.py`, and a failing `assert` is rendered on the offending line — handy for debugging a failing test. Pass arguments yourself (`from_pytest(nodeid, x=3)`) to bypass fixtures entirely, the escape hatch for parametrized tests or fixtures too heavy to spin up. If a bare node id matches several tests, `from_pytest` refuses to guess and asks for a specific `...::test_bar[case]` id (or manual args). Class-based and `async def` tests aren't supported yet. Requires pytest (`pip install wigglystuff[pytest]`).
- `EsmWidget`: render an inline [ES module](https://developer.mozilla.org/docs/Web/JavaScript/Guide/Modules) in a notebook. It is a thin, library-agnostic runner — you hand it a module that follows the standard anywidget contract (`export default { render }`) and it loads that module in the browser. Because it is loaded as a *real* ES module, top-level `import` statements work, so you can pull any library straight from a CDN (motion.dev, Observable Plot, d3, chart.js, three.js, …). The `data` traitlet is a JSON-able value synced both ways; changing it fires `change:data` in the browser but does **not** re-run `render`, so the module decides how to react — animation libraries can *tween* toward the new state while chart libraries can *redraw*. The module source (`code` or `src`) can be inline JavaScript, a local `.js` file path, or an `http(s)://` URL — files and URLs are resolved in Python at construction time. JS runtime errors surface via the `error` traitlet.

## [0.5.16] - 2026-07-14

### Added

- `ManimWeb`: run a [manim-web](https://github.com/maloyan/manim-web) (browser Manim) scene inline in a notebook. The engine is loaded from a CDN and your scene JavaScript runs with the `manim` namespace, a `container` element, and `width`/`height`/`model` in scope. Use manim-web's own `Player` for a full playback UI (play/pause, scrub timeline with segment markers, speed, fullscreen, export; `autoPlay`/`loop`/`backgroundColor` options). The scene source (`code` or `src`) can be inline JavaScript, a local `.js` file path, or an `http(s)://` URL — files and URLs are resolved in Python at construction time, so the browser always gets plain JS. JS runtime errors surface via the `error` traitlet.
- `AsyncFlow`: a new widget that traces a single `async` run live and renders it as a swimlane timeline. `await AsyncFlow.trace(main())` runs the coroutine on the notebook's own event loop and streams task activity into the widget as it happens — one lane per task, solid bars for running and hatched bars for suspended-at-`await`, with child tasks nested under their parent (depth-first) and per-task timing (ran vs waited) on hover. Capture uses `asyncio` task hooks plus `sys.monitoring`, so it requires Python 3.12+.
- `FramePlayer`: play a sequence of images as an inline, optionally-looping "video". Accepts PIL images, file paths, URLs, bytes, base64 strings, or matplotlib figures (mixed is fine), and renders the current frame with play/pause/loop controls and a scrubber — no second cell that reads a slider value and re-renders.

## [0.5.15] - 2026-07-14

### Fixed

- `ParallelCoordinates`: dragging an axis label no longer occasionally replaces the chart with HiPlot's `Cannot read properties of null (reading 'pos')` error fallback.
- Require Python 3.11+ (`tomllib`, imported in `__init__.py`, is only available in the stdlib from 3.11 onward). Fixes #267.

## [0.5.14] - 2026-07-14

### Changed

- `ParallelCoordinates` now uses compact Annotation-style controls, readable system typography, and clearer selected-count text. Draggable column headings show a persistent six-dot grip, `grab` feedback, and single-line truncation with the full column name and reorder instructions available on hover.

## [0.5.13] - 2026-07-06

### Added

- `LiveEdit`: click a numeric loop-trace column header to plot that variable across passes (iteration on X, value on Y) as an inline line chart. A plain click starts a fresh single-series chart; ⌘/Ctrl-click overlays a column onto the current chart (shared Y-axis); Shift-click stacks a new chart below, sharing the X-axis so panels at different scales line up by iteration. A small `×` clears the chart. Only columns whose every pass parses to a finite float are chartable, and charts render as lightweight SVG with no new dependencies.
- `LiveEdit`: new `float_precision` argument (and traitlet) rounds float cells to the given number of significant figures to keep wide tables readable; charts keep full precision. Defaults to `None` (exact `repr`).
- `LiveEdit`: new `visible_columns` argument (and traitlet) restricts the trace tables to a chosen subset of variables; the default empty list shows everything. Applied in the browser, so it updates without re-running the traced function.
- `LiveEdit`: trace values with a rich HTML representation now render inline in the trace panel instead of their plain `repr`. Setup variables, loop-pass cells, and the return value each check the value for marimo's `_display_`/`_mime_` protocols and IPython's `_repr_html_` (duck-typed, so no hard dependency on marimo/pandas/numpy) and, when found, render the HTML in the widget. Values without a rich representation are unchanged. Oversized payloads (>100 KB) fall back to `repr`.

### Changed

- `LiveEdit`: the widget now grows horizontally to fit its content by default so wide tables and charts widen the whole widget (and the host page/marimo scrolls) instead of a cramped inner horizontal scrollbar. Set a positive `width` to cap it. Height stays bounded so the source and trace columns scroll independently and the function stays visible while the trace scrolls.
- `LiveEdit`: when a traced function raises, the failure is now anchored at the point where it happened instead of only floating in a summary box at the top. The failing source line is highlighted with an inline error message, the trace row (loop pass) where execution stopped is marked with a `✗`, and the return chip reads `raised <ErrorType>` rather than the misleading `returned None`. The compact top summary box is kept as well.

### Fixed

- `LiveEdit`: the default height now auto-fits the function's line count with a 520px floor, and an explicit `height=` is honored as a hard box size.

## [0.5.12] - 2026-07-06

### Added

- `LiveEdit`: new read-only function trace widget. `LiveEdit.inspect_run(fn, *args, **kwargs)` instruments one Python function body, runs it once with private Python-side args, and renders setup values, loop passes, nested loop traces, and return values with source-linked hover highlighting. Trace values are captured as `repr(...)` strings so optional objects such as numpy arrays remain supported without adding hard dependencies.
- `GridDraw`: new drawable square-grid widget for marking dots on grid intersections and orthogonal unit line segments between adjacent intersections. It supports dot, line, and eraser modes; click toggles a single item, drag paints a stroke, undo restores each completed gesture, clear is undoable, and a local theme toggle can force light/dark rendering. The synced data is plain Python-friendly structure: `dots` as `[[row, col], ...]` and `lines` as `{"from": [r, c], "to": [r, c], "width": int}` dictionaries. `line_width` accepts either a fixed integer or a list of widths that enables the toolbar picker.

### Changed

- `GridDraw`: toolbar controls now show Lucide-style icons next to their text labels, keeping the labels visible while making the drawing modes and actions easier to scan.
- `Excalidraw`: now fits the loaded scene to the viewport on open, so drawings
  saved while zoomed out reopen at the right scale instead of clipping. Capped at
  100% zoom — it zooms out to show everything but never zooms in past actual
  size — and leaves a small margin so content doesn't hug the canvas edges.
  (#252, closes #251)

### Fixed

- `GridDraw`: line and eraser drag strokes now trace the actual grid segments crossed by the pointer path, avoiding under- or over-extension when the cursor passes through segment centers or near intersections.

## [0.5.11] - 2026-06-30

### Added

- `TangleSlider`: click the value to type it in directly. Clicking (without dragging) turns the value into an inline input — type a number, press `Enter` to confirm or `Escape` to cancel; clicking outside also cancels. The typed value respects the slider's `min_value`/`max_value` (out-of-range values are clamped) and `step` (snapped to the step grid); non-numeric input restores the previous value. Dragging still works exactly as before. Click-to-type is only enabled for linear sliders, not those built with an explicit `steps` list. (#255)

## [0.5.9] - 2026-06-08

### Added

- `Excalidraw.save()` now remembers the path and can be called with no argument. Widgets created with `Excalidraw.from_file(...)` capture their source path, so a bare `save()` writes back to the file they were loaded from; passing a path saves there and remembers it for subsequent bare calls. `save()` now returns the absolute destination (shown as the cell output in marimo) so it's always clear where the file landed. The widget still never writes on its own — drop `save()` into its own marimo cell and marimo re-runs it whenever the widget changes, so the file tracks what you draw. There is no file-watching or bidirectional sync; the notebook stays the source of truth.

### Fixed

- `Excalidraw`: copy/paste now works inside marimo. Excalidraw's clipboard handlers check focus and pointer position with `document.activeElement` and `document.elementFromPoint`, neither of which pierces the shadow DOM marimo mounts widgets in — so copy, cut, and paste (both into and out of the widget, including to/from excalidraw.com) silently bailed. The loader now installs a shadow-DOM-aware shim over those two APIs while a widget is mounted. It's scoped to shadow roots that actually host an Excalidraw instance, so focus/clipboard behavior elsewhere on the page (marimo code cells, other widgets) is unchanged. (#247)

### Changed

- Docs: every widget's reference example now shows the marimo idiom `mo.ui.anywidget(...)` (wrapping the widget so its state syncs reactively in marimo), matching how the `demos/` notebooks use these widgets. The examples are auto-generated from class docstrings, so the rendered reference pages stay in sync.
- `CellTour`: now works in marimo app mode (`marimo run` / molab) in addition to edit mode. No behavior change in the widget itself — marimo `>= 0.23` started rendering `.marimo-cell` and `[data-cell-name]` on cell containers in app mode, which is what `CellTour`'s step selectors already target. The docstring, reference page, and bundled demo (`demos/celltour.py`) have been updated to reflect this; the demo is reworked so its tour steps point at cells with visible output (so it makes sense when opened via `marimo run`) and its PEP 723 header now pins `marimo>=0.23`.

## [0.5.8] - 2026-06-04

### Added

- `Excalidraw`: a new widget that embeds an [Excalidraw](https://excalidraw.com) whiteboard. Sketch shapes, arrows, text, and freehand drawings on an infinite canvas; the scene (`elements` / `appState` / `files`) syncs back to Python on the `scene` traitlet (debounced via `sync_throttle_ms`), and `get_pil()` returns a PIL image of the drawing so you can pass it forward (e.g. into a multimodal model). The hamburger menu and shape Library are hidden (their file/export/library actions don't apply to an embedded surface), and the canvas theme defaults to light — pass `theme="dark"` to pin it dark, or `theme=""` to follow the notebook. Following the library's other drawing widgets, nothing is written to disk automatically — preload a scene with `Excalidraw(scene=...)`, persist with `save(path)`, and reload with `Excalidraw.from_file(path)`. Excalidraw + React (~8MB) are loaded from a CDN the first time the widget renders rather than bundled into the package, so the widget needs network access and does not work fully offline.
- New `Space-Filling Curves` example notebook (`demos/curve-filling.py`) added to the docs gallery. It uses `CircularRangeSlider` to drive a matplotlib explorer comparing Morton, Hilbert, and Moore curves — drag the seamless dial to highlight a wrapping window of ranks along the curve.

### Changed

- `Paint`: the color swatch is now hidden while the eraser or rainbow-spray tool is active, since neither uses a chosen color (the eraser removes pixels and the rainbow tool randomizes hue per particle). The thickness slider still shows for those tools. The rainbow tool's toolbar icon is now a cluster of scattered multi-colored dots instead of mono-color concentric arcs, so it reads as "rainbow" at a glance.

## [0.5.7] - 2026-05-28

### Fixed

- `CircularSlider` and `CircularRangeSlider`: rewrite the front end in SVG instead of canvas. Removes a same-color residue artifact where previous arc positions stayed visible on the track, caused by re-renders stacking canvases on top of one another.

## [0.5.6] - 2026-05-28

### Added

- `CircularSlider` and `CircularRangeSlider`: new dial-style widgets for picking a value or a span on a full circle. The API mirrors `mo.ui.slider` / `mo.ui.range_slider` (`start`, `stop`, `step`, `value`) and the ring is configurable via `size`, `thickness`, `show_value`, and `color`. Dragging inside the filled arc of a range slider translates the whole `(low, high)` window, wrapping freely around the 12 o'clock seam — a wrap-around range is represented as a tuple where `low > high`. Dragging either handle past the other also wraps (no swap). Construction tolerates `(high, low)` for backwards-compatible "min/max" calls by sorting on init. The numeric readout is rendered below the dial. Construction raises `ValueError` when `size < 2 * thickness + 30` so callers don't get a silently broken render. The `color` traitlet accepts any CSS color string (`"#ef4444"`, `"tomato"`, etc.) and recolors the fill arc and handle border; leave it empty to follow the light/dark theme. The `label` traitlet places a text label above the dial — matching the `label=` parameter on `mo.ui.slider`.

## [0.5.5] - 2026-05-27

### Added

- `BezierCurve` and `CurveEditor`: drag empty space inside the axes frame to pan and use the mouse wheel to zoom toward the cursor. The view transform is pixel-space only — `x_bounds` / `y_bounds` are unchanged and no view state is synced to Python. Grid lines and axis ticks recompute against the visible range as you zoom, and the curve is clipped to the plot area so it no longer spills past the axes.

### Fixed

- `BezierCurve` and `CurveEditor`: editing the curve (dragging a control point, double-clicking to add or remove a point, or toggling `closed`) no longer pauses playback. The playhead now continues across the new curve shape, matching the existing behaviour when changing the curve type or tension. Progress-slider scrubbing still pauses, since scrubbing `t` directly fights the timer.

## [0.5.4] - 2026-05-26

### Added

- `BezierCurve` and `CurveEditor`: new `show_axes` trait toggles numeric tick marks and labels on the x and y axes (off by default — no visual change for existing users). When enabled, margins expand to fit the labels and ticks are auto-picked from the configured `x_bounds` / `y_bounds`.
- `BezierCurve` and `CurveEditor`: new `samples` trait emits a `[{x, y}, ...]` list of `n_samples` points along the rendered curve in data coordinates, throttled by the existing `sync_throttle_ms`. `n_samples` defaults to 100 and must be at least 2. Useful for iterating over the curve in Python without re-deriving the interpolation.

### Fixed

- `AnnotationWidget.actions` now only describes the main action buttons (`previous`, `accept`, `fail`, `defer` by default). Save remains a separate footer control governed by `show_save`; when `show_save=False`, save shortcuts are hidden and ignored.
- `AnnotationWidget` now derives the default keyboard mapping from `actions`, assigning action buttons to number keys in order while keeping `s` for save and `m` for mic.
- `AnnotationWidget` now derives the default gamepad mapping from `actions`, assigning action buttons to gamepad indices in order followed by save and mic.

## [0.5.3] - 2026-05-22

### Added

- `CurveEditor` widget for editing chart-space knots with D3 curve interpolators. Open curves store points in x order, while closed curves preserve drawing order so double-clicked points are appended to the loop. Curves can render with linear, step, basis, natural, cardinal, Catmull-Rom, monotone-x, and bump-x curves. A bottom progress control emits `t`, `x`, and `y` from the rendered path, with optional closed-path and loop playback controls.
- `BezierCurve` widget for editing arbitrary-degree Bezier curves in notebooks. Drag control points, double-click to add points, optionally close the curve, and play through `t` with loop-aware playback.

## [0.5.2] - 2026-05-21

### Changed

- **Breaking:** `GraphWidget` sizing semantics now match the trait names. `width` defaults to `None` (the SVG fills its container's width and reflows when the container resizes); passing an integer pins it to that exact pixel size regardless of container. `height` defaults to `400` and is always an exact pixel height. Previously `width=800, height=600` only set an aspect-ratio hint because the CSS forced `max-width: 100%; height: auto` over the JS-set dimensions.
- McNugget demo (`demos/mcnugget_graph.py`): hover path now brackets totals (`0 → +6 → [6] → +9 → [15]`) so they read distinctly from the `+box` deltas. Added two control checkboxes: _Color arcs by box size_ (per-denomination palette) and _Color nodes by inbound arcs_ (light→dark gradient by in-degree). Node payload now carries `in_degree` in `data`.

## [0.5.1] - 2026-05-20

### Added

- `GraphWidget` for programmatic force-directed graph visualization. Nodes and edges can be supplied from Python with optional names, sizes, colors, and metadata; browser interactions support zoom, pan, drag, hover tooltips, bounded or unbounded layouts, and selection synced back to Python.
- `GraphWidget.attach_node(...)` for adding a new or existing node together with its connecting edge, plus `detach_node(...)` for removing attached edges while optionally deleting the node. The frontend now initializes newly connected nodes near their existing endpoint and restarts the force simulation gently, avoiding full-layout jumps for incremental graph updates.
- `GraphWidget.hovered_node` traitlet exposes the id of the node currently under the cursor (`None` when no node is hovered), so Python can react to hover without needing a click.
- Added the `McNugget sums` demo (`demos/mcnugget_graph.py`) — a `GraphWidget` + `PlaySlider` notebook that breadth-first-searches reachable totals from a configurable set of box sizes.
- Added a "Random growth graph" section to `demos/graphwidget.py` — at each step a new node is added and connected to a random existing node, scrubbed with `PlaySlider`.
- Added the `Hypercube` example (`demos/hypercube.py`, linked from the docs gallery Examples section) showing how the force layout unfurls $Q_n$ — $Q_3$ snaps into a cube, $Q_4$ projects into a tesseract. Sliders pick dimension $n$ and node size; nodes are colored by popcount, edges by which bit position the endpoints differ in.

## [0.5.0] - 2026-05-15

### Removed

- **Breaking:** `DiffViewer` widget has been removed. The `@pierre/diffs` library it depended on embedded 298 TextMate grammars, making `diff-viewer.js` 9.3 MB (62% of all static assets). The wheel drops from ~3.1 MB to ~1.5 MB compressed as a result. (Issue #217)

### Changed

- **Breaking:** `PulsarChart` has been renamed to `RidgelineChart` — the conventional name for stacked-waveform "Joy Division" plots. The module also moved from `wigglystuff.pulsar_chart` to `wigglystuff.ridgeline_chart`. Update imports accordingly: `from wigglystuff import RidgelineChart`. (Issue #87)
- `numpy` and `pillow` are now optional dependencies. Install `wigglystuff[all]` to get both, or `wigglystuff[numpy]` / `wigglystuff[pillow]` individually. Widgets that require these libraries import them at function scope.
- Widgets that use d3 (`Treemap`, `EdgeDraw`, `Neo4jWidget`, `ScatterWidget`, `SplineDraw`, and `RidgelineChart`) now import only the specific `d3-*` submodules they need instead of bundling the full `d3.min.js`. Total shipped JS for these widgets drops from ~2.7 MB to ~225 KB (–92%).

### Fixed

- `Treemap` no longer fails to render with `Error rendering anywidget: h is not a function`. The tree-shaking rewrite left two local variables (`hierarchy`, `color`) shadowing same-named d3 imports inside `js/treemap/widget.js`; the imports are now aliased so the d3 functions are reachable at the call sites.

## [0.4.4] - 2026-05-13

### Changed

- `Paint` toolbar now shows a thickness slider next to the color picker when the marker, eraser, or rainbow tool is selected, so you can adjust stroke/spray size on the fly. The pencil/brush stays at a fixed thin stroke, and each tool remembers its own thickness. The rainbow tool icon is now monochrome (inherits `currentColor`) to match the rest of the toolbar.

## [0.4.3] - 2026-05-13

### Added

- Added "Paint Scatter" example (`demos/paint-scatter.py`, linked from the docs gallery) showing a `Paint` canvas driven by a marimo `mo.ui.refresh` loop. The notebook contains two demos sharing the same update technique: a pointillist scatter that blooms colorful dots around dark pixels, and a colored Conway's Game of Life that seeds from the user's strokes and drifts each cell's color toward the mean of its live neighbors with a touch of noise. The gallery link now boots the example in molab WASM (`…/paint-scatter.py/wasm`).
- `Paint.replace_with_pil(img)` replaces the canvas contents with a PIL Image after construction. Wipes any existing strokes (the canvas has no separate background layer); resizes to the widget's `(width, height)` if needed.
- `Paint(rainbow_brush=True)` adds an optional spray tool to the toolbar that scatters randomly-colored particles around the cursor — useful for generating noisy, multi-color inputs/masks for image models.

## [0.4.2] - 2026-05-12

### Added

- Added "Complex Plane Roots" to the docs gallery Examples section, linking a molab notebook by Simone Conradi that uses `ChartPuck` to visualize the argument of a monic polynomial on the complex plane.
- Added "Steam Deck Annotations" example (`demos/steamdeck.py`, linked from the docs gallery with a thumbnail) showing how to drive `AnnotationWidget` from a Steam Deck by mapping its buttons to keyboard keys through Steam Input, with a separate `KeystrokeWidget` section for inspecting what each button emits.
- `AnnotationWidget` `keyboard_mapping` now accepts chord bindings such as `"cmd+shift+s"` or `"ctrl+alt+x"`. Tokens are `+`-separated and case-insensitive; modifier aliases (`command`/`meta`, `control`, `option`) are accepted. When both a bare-key binding and a chord binding could match the same keypress, the chord wins so that e.g. `"cmd+s"` takes precedence over `"s"`.

### Changed

- Converted docs gallery screenshots from PNG to WebP, shrinking `docs/assets/` from 6.2 MB to 1.2 MB (82% smaller).
- `AnnotationWidget` shortcuts panel now renders arrow keys as `←` `↑` `→` `↓`, modifiers as `⌘` `⇧` `⌃` `⌥` (macOS canonical order), and the spacebar as the word `Space` — instead of the raw `event.key` strings like `arrowleft` or an invisible space character.
- `AnnotationWidget`: a keyboard shortcut mapped to the `"mic"` action is now **push-to-talk** — recording starts on keydown and stops on keyup. The mic button still toggles on click. This makes spacebar / Steam-Deck button setups behave the way you'd expect ("hold to talk").

### Fixed

- `AnnotationWidget` voice-input no longer duplicates finalized phrases. The `change:note` listener was synchronizing the session base text (`noteBeforeSpeech`) on every note write, including writes from the widget's own `onresult` handler — so on the next speech-result event the cumulative `event.results` array re-concatenated every already-finalized phrase onto the new base. Only sync `noteBeforeSpeech` from `change:note` when not actively recording.

## [0.4.1] - 2026-05-01

### Changed

- `Matrix`, `ModuleTreeWidget`, and `ChartSelect` now render a small "graduated to marimo core" hint in the cell when instantiated inside a marimo notebook, with a link to the equivalent marimo built-in (`marimo.ui.matrix`, marimo's built-in PyTorch formatter, and `marimo.ui.matplotlib` respectively). The widgets continue to work as before in Jupyter and other anywidget hosts.

## 0.4.0

### Fixed

- `EnvConfig` no longer syncs configured secret values in its exported anywidget state, preventing marimo static HTML exports from embedding environment-loaded or manually entered secrets.

### Removed

- `WandbChart` widget removed due to a security concern: marimo's static HTML export embeds all anywidget traitlets, which would leak the user-supplied `api_key` into any exported notebook.

## [0.3.5] - 2026-04-23

### Added
- `Treemap` widget: new `hovered_path` traitlet that updates as the cursor moves over rectangles, allowing Python code to react to hover without requiring a click.

## [0.3.4] - 2026-04-23

### Added
- `Treemap` widget: zoomable hierarchical treemap rendered on canvas with hover previews, clickable path navigation, leaf selection, contextual recoloring during zoom, and constructors for direct `{name, value, children}` dicts, path mappings, records, or dataframes. Ported from the Svelte components in `koaning/pytest-duration-insights`.
- `NestedTable` widget: recursive expandable table showing name, summed value, and share of the root total. Shares the same hierarchy shape and `from_paths` / `from_records` / `from_dataframe` classmethods as `Treemap`.

## [0.3.3] - 2026-04-15

### Added
- `TangleSlider` now accepts an optional `steps` parameter for non-linear value ranges. When provided, the slider cycles through the explicit list of values instead of using linear min/max/step bounds.

### Fixed
- ProgressBar demo now uses `.widget.value` to correctly update progress when wrapped with `mo.ui.anywidget()`.
- ProgressBar gallery links in docs and README now point to the correct `demos/progressbar.py` instead of `demos/htmlwidget.py`.

## [0.3.2] - 2026-04-10

### Added
- `ApiDoc.to_markdown()` method to export API documentation as a Markdown string for use in READMEs.
- `ApiDoc` signature block now has Python syntax highlighting, matching code blocks in docstrings.

### Changed
- Moved example notebooks from `examples/` to `demos/` folder.
- Added infinite zoom (Droste effect) example to the docs gallery.
- `Paint` toolbar icons: replaced generic pencil icons with a distinct pen (brush) and highlighter (marker) to make the tools easier to tell apart.

## [0.3.1] - 2026-03-25

### Fixed
- Removed accidental `python-dotenv` and `umap-learn` core dependencies that were not used by any widget.

## [0.3.0] - 2026-03-24

### Changed
- `Paint` widget redesigned: replaced MS Paint window chrome with a minimal toolbar (brush, marker, eraser, undo, clear, color picker). Dropped Tailwind CSS dependency in favor of scoped CSS variables with dark mode support.

### Fixed
- `Paint` canvas now respects the `width` and `height` traitlets instead of expanding to fill the host container.
- `Paint` with `init_image` now resizes the image to match target dimensions upfront, so `get_pil()` returns the correct resolution before the first stroke.

## [0.2.40] - 2026-03-24

### Added
- `PlaySlider` now has a `values` property that returns all discrete values in the range, useful for pre-caching downstream results before hitting play.
- `ParallelCoordinates` now exposes a `selections` property that returns the full filtering state: completed Keep/Exclude steps plus the active brush, enabling decision-tree-style filtering audit trails.
- `ParallelCoordinates` now has `keep()`, `exclude()`, and `restore()` methods for programmatic control from Python.

### Fixed
- `PlaySlider` no longer produces floating-point rounding artifacts (e.g., `0.30000000000000004`) when using fractional step values. Both the displayed label and the synced Python value are now rounded to the step's precision.
- `ParallelCoordinates` axis tick labels no longer get highlighted during brush/drag interactions.

## [0.2.39] - 2026-03-17

### Changed
- `forecast_chart` demo now uses `AltairWidget` for flicker-free updates in marimo wasm mode.

### Fixed
- `AltairWidget` now embeds the full spec (with data) on initial render, fixing blank charts for layered specs with named datasets.

## [0.2.38] - 2026-03-17

### Added
- `forecast_chart` utility function that creates a time series Altair chart with a robust exponential forecast.

### Changed
- `ParallelCoordinates` default height reduced from 600px to 500px so the widget fits within marimo's default output clip without scrolling.

## [0.2.37] - 2026-03-12

### Added
- `ThreeWidget` now supports per-point opacity via an optional `opacity` key in each data dict (0.0–1.0, defaults to 1.0).
- `ThreeWidget` now accepts `xlim`, `ylim`, and `zlim` parameters to fix axis bounds instead of auto-fitting from data.
- `ThreeWidget` now accepts `camera_azimuth` and `camera_elevation` parameters (in degrees) to control the initial viewing angle.
- `ParallelCoordinates` now accepts a `color_map` parameter to assign explicit CSS colors to categorical values (e.g. `color_map={"a": "red", "b": "#0000ff"}`). Any CSS color format is accepted and auto-converted.
- `PlaySlider` widget: a range slider with a play/pause button that auto-advances the value on a configurable interval. Supports looping, step size, interval control, and light/dark themes.

### Fixed
- `ThreeWidget` no longer resets the camera on data updates, so auto-rotation continues smoothly when points change.
- `ParallelCoordinates` categorical color assignment is now deterministic regardless of data row order. Unique values are sorted before mapping to the default palette.
- `ParallelCoordinates` Keep/Exclude/Restore buttons now correctly update `filtered_indices`, `filtered_data`, and `selected_indices`. Previously only axis brush drags were tracked; the Keep/Exclude row filtering events from HiPlot were silently dropped.

## [0.2.36] - 2026-03-05

### Fixed
- `TangleSlider`, `TangleChoice`, and `TangleSelect` now respond to external model changes via `model.on("change:...")` handlers. Previously, setting traitlet values from Python or external frameworks (e.g., Panel) had no effect on the displayed widget.
- `TangleChoice` ESM read `model.get("value")` instead of `model.get("choice")` at initialization, causing the initial index lookup to always fall back to 0.
- Removed stray `console.log` from `TangleSlider` ESM.

## [0.2.35] - 2026-03-05

### Added
- `AnnotationWidget` now has a `disabled` traitlet. When set, accept/fail/defer buttons, mic, and note input are greyed out while previous and save remain active.
- `AnnotationWidget` now has a `show_save` traitlet. When `False`, the save button is hidden and removed from the keyboard/gamepad shortcut reference.

### Changed
- `ProgressBar` redesigned with a cleaner, minimal style: flat dark background, configurable fill color, simpler border radius, and text below the bar. Removed gradient fills, box shadows, inset borders, and percentage overlay from the old design.
- `ProgressBar` now supports `color`, `show_text`, `width`, and `height` traitlets for customization.
- `ProgressBar` demo moved into its own standalone notebook (`demos/progressbar.py`), separated from the HTML widget demos.
- Annotation demo: progress bar now tracks position and shows 8/8 when all items are annotated.
- Annotation demo: annotation dict is now updated immutably via dict spread instead of mutating state in place.

## [0.2.34] - 2026-03-02

### Fixed
- `ParallelCoordinates` now works with polars DataFrames. The polars `to_dicts` check is performed before the pandas `to_dict` check, since polars also exposes `.to_dict`.

### Changed
- `ParallelCoordinates` demo notebook and docstring examples now use polars instead of pandas.

### Added
- New `examples/fashion-mnist-parallel-coords.py` example notebook showing PCA + parallel coordinates on Fashion MNIST.

## [0.2.33] - 2026-02-27

### Added
- `ParallelCoordinates` added to the docs and gallery.
- `SplineDraw.redraw()` method to retrigger spline recomputation or swap in a new `spline_fn` at runtime.

## [0.2.32] - 2026-02-25

### Added
- New `SplineDraw` widget for drawing scatter points with a Python-computed spline curve overlay. Accepts any callable with signature `(x, y) -> (x_curve, y_curve)` for flexible curve fitting.
- New `ApiDoc` widget for rendering Python class and function API documentation directly in notebooks. Introspects signatures, parameters, docstrings, methods, and properties via `inspect`. Features collapsible sections, colored badges, syntax highlighting, and light/dark theme support.

### Fixed
- `KeystrokeWidget` canvas now includes a generic `monospace` fallback in the font stack.
- `AltairWidget` now correctly renders layered and concatenated Altair charts that use multiple datasets.

## [0.2.30] - 2026-02-19

### Added
- New `AltairWidget` for flicker-free Altair chart rendering. Uses Vega's persistent View API to patch data in-place via changesets, preserving interactive state across updates.

### Changed
- `ScatterWidget` is now re-exported from the [`drawdata`](https://github.com/koaning/drawdata) package. The import `from wigglystuff import ScatterWidget` still works.

## [0.2.29] - 2026-02-19

### Added
- New `DiffViewer` widget for rich file diffs. Supports split and unified diff styles with syntax highlighting, dark mode, and configurable expansion of unchanged lines.

## [0.2.28] - 2026-02-16

### Added
- New `ScatterWidget` for painting multi-class 2D datasets directly in notebooks. Includes class selection, brush controls, undo/reset, and synced point data with helper conversions (`data_as_pandas`, `data_as_polars`, `data_as_X_y`).
- `ScatterWidget.n_classes` is now validated on assignment (not only at construction), enforcing the `1..4` range.
- `ScatterWidget.data_as_X_y` now returns stable output shapes based on configured mode (`n_classes==1` for regression, `n_classes>1` for classification).

## [0.2.27] - 2026-02-12

### Fixed
- `ChartSelect.from_callback` and `ChartPuck.from_callback` now use proper init proxies so user callbacks that call widget helpers during the initial render no longer crash.

## [0.2.26] - 2026-02-12

### Fixed
- `ChartSelect` and `ChartPuck` now work correctly with log-scale matplotlib axes. Coordinate transforms are done in Python (log10 space) so the JS frontend uses plain linear math.

## [0.2.25] - 2026-02-11

### Added
- `Neo4jWidget` for interactive Neo4j graph exploration. Features Cypher query input with schema-aware autocomplete, force-directed graph visualization, node/edge selection (click, ctrl-click, lasso), double-click node expansion, and zoom/pan navigation. Requires a `neo4j` driver instance.

## [0.2.24] - 2026-02-09

### Added
- `WandbChart` widget for live wandb run visualization with configurable smoothing (rolling mean, EMA, gaussian). Supports multiple runs, auto-polling, and an interactive smoothing dropdown.

### Fixed
- Removed `wandb` from core dependencies. It was accidentally added as a required dependency but should only be an optional extra (`pip install wigglystuff[wandb]`).

## [0.2.23] - 2026-02-09

### Added
- `ModuleTreeWidget` for visualising PyTorch `nn.Module` architecture as an interactive tree with parameter counts, shapes, and trainable/frozen/buffer badges.
- Shared parameter detection: tied weights are marked with a "shared" badge and counted only once in totals.
- Lazy parameter detection: `nn.LazyLinear` and similar modules show a "lazy" badge with "uninitialized" instead of a shape.
- Unregistered module detection: warns when `nn.Module` instances are stored in plain Python lists instead of `nn.ModuleList`.
- Convenience properties: `total_param_count`, `total_trainable_count`, `total_size_bytes`.
- New "molab" gallery section for widgets that depend on 3rd party packages.

### Changed
- Removed `**kwargs` from `ModuleTreeWidget.__init__`.

## [0.2.22] - 2026-02-08

### Added
- `ChartPuck.puck_color` now accepts a list of CSS colors for per-puck coloring. A single string still applies to all pucks.
- New `throttle` parameter on `ChartPuck` to control how often puck positions sync to Python during drag. Set to an integer for millisecond throttling or `"dragend"` to sync only on release.

### Changed
- Removed `**kwargs` from `ChartPuck.__init__`; all parameters are now explicit.

## [0.2.21] - 2026-02-04

### Added
- ColorPicker now shows the hex value next to the input by default (toggle with `show_label`).

### Fixed
- ColorPicker now keeps its hex label in sync when the color is updated programmatically.

## [0.2.20] - 2026-02-02

### Added
- `EnvConfig.get(name, default=None)` method for dict-like access.
- Optional `variables` parameter to `EnvConfig.require_valid()` to check only a subset of configured variables.

## [0.2.19] - 2026-01-29

### Added
- New `ChartSelect` widget for interactive region selection on matplotlib charts. Supports box and lasso modes, returns selection coordinates in data space, and includes helper methods (`get_mask()`, `get_indices()`, `get_bounds()`, `contains_point()`). Also supports `from_callback()` factory for auto-updating charts.

## [0.2.18] - 2026-01-26

### Fixed
- Removed `scikit-learn` from core dependencies. It was accidentally added but is only used by the optional `ChartPuck.export_kmeans()` method.

## [0.2.17] - 2026-01-26

### Changed
- **Breaking:** `ChartPuck.from_callback` now passes the widget to the draw function instead of scalar coordinates. Signature changed from `draw_fn(ax, x, y)` to `draw_fn(ax, widget)`, giving access to all puck positions via `widget.x` and `widget.y`.

### Added
- New `redraw()` method on `ChartPuck` for manually triggering chart re-renders when external state changes. Only available for widgets created via `from_callback()`.
- Added Step, Nearest, Quadratic, and Barycentric interpolation methods to the ChartPuck spline demo.

## [0.2.16] - 2026-01-20

### Added
- New `ChartPuck` widget for overlaying draggable pucks on matplotlib charts. Supports single or multiple pucks, customizable styling, a `from_callback` factory for auto-updating charts, and `export_kmeans()` for using puck positions as KMeans initial centroids.

## [0.2.15] - 2026-01-20

### Added
- Playwright browser integration tests for `SortableList` widget, verifying full browser-to-Python round-trip communication.
- New `test-browser` optional dependency group and CI workflow for running browser tests with marimo.

### Removed
- Removed unused `pydantic-ai` dependency that was pulling in `openai` and breaking WASM demos.

## [0.2.14] - 2026-01-19

### Fixed
- `EnvConfig` now displays values in input fields even when validation fails.
- Removed footer color changes in `EnvConfig`. Individual row highlighting is now the sole status indicator.

## [0.2.13] - 2026-01-15

### Added
- New `EnvConfig` widget for environment variable configuration with validation. Displays a form UI for setting API keys with password-style masking, optional validator callbacks, and a `require_valid()` method to block execution until all variables are configured.

## [0.2.12] - 2026-01-12

### Added
- New `TextCompare` widget for side-by-side text comparison with match highlighting. Features hover-based highlighting that syncs between panels and configurable minimum match length via `min_match_words`.

## [0.2.11] - 2026-01-08

### Added
- New `PulsarChart` widget for stacked waveform visualization. Features clickable rows with selection state synced back to Python, customizable overlap, stroke width, fill opacity, and peak scale.

## [0.2.10] - 2026-01-07

### Fixed
- Fixed "Maximum call stack size exceeded" error when rendering `Slider2D` on latest marimo. The widget had an infinite loop where model change handlers would trigger redraws that updated the model again.
