# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
