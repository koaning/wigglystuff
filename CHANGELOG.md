# Changelog

All notable changes to this project will be documented in this file.

## [0.2.22] - 2026-02-08

### Added
- `ChartPuck.puck_color` now accepts a list of CSS colors for per-puck coloring (e.g., `puck_color=["red", "green", "blue"]`). A single string still applies to all pucks.
- New `throttle` parameter on `ChartPuck` to control how often puck positions sync to Python during drag. Set to an integer for millisecond throttling (e.g., `throttle=100`) or `"dragend"` to sync only on release.

### Changed
- Removed `**kwargs` from `ChartPuck.__init__`; all parameters are now explicit.

## [0.2.21] - 2026-02-04

### Added
- ColorPicker now shows the hex value next to the input by default (toggle with `show_label`).

### Fixed
- ColorPicker now keeps its hex label in sync when the color is updated programmatically (e.g., demo button updates).

## [0.2.20] - 2026-02-02

### Added
- `EnvConfig.get(name, default=None)` method for dict-like access that returns a default value instead of raising `KeyError`.
- Optional `variables` parameter to `EnvConfig.require_valid()` to check only a subset of configured variables, allowing some to remain unset.

## [0.2.19] - 2026-01-29

### Added
- New `ChartSelect` widget for interactive region selection on matplotlib charts. Supports box and lasso (freehand) selection modes, returns selection coordinates in data space, and includes helper methods (`get_mask()`, `get_indices()`, `get_bounds()`, `contains_point()`) for filtering data points. Also supports `from_callback()` factory for auto-updating charts.

## [0.2.18] - 2026-01-26

### Fixed
- Removed `scikit-learn` from core dependencies. It was accidentally added as a required dependency but is only used by the optional `ChartPuck.export_kmeans()` method. Users of this method should install with `pip install wigglystuff[test]`.

## [0.2.17] - 2026-01-26

### Changed
- **Breaking:** `ChartPuck.from_callback` now passes the widget to the draw function instead of scalar coordinates. The signature changed from `draw_fn(ax, x, y)` to `draw_fn(ax, widget)`, giving access to all puck positions via `widget.x` and `widget.y` lists.

### Added
- New `redraw()` method on `ChartPuck` for manually triggering chart re-renders when external state changes (e.g., dropdown selections). Only available for widgets created via `from_callback()`.
- Added Step, Nearest, Quadratic, and Barycentric interpolation methods to the ChartPuck spline demo.

## [0.2.16] - 2026-01-20

### Added
- New `ChartPuck` widget for overlaying draggable pucks on matplotlib charts. Allows interactive selection of coordinates in data space with automatic conversion between pixel and data coordinates. Supports single or multiple pucks, customizable styling (color, radius), a `from_callback` factory method for charts that auto-update when the puck moves, and an `export_kmeans()` method to use puck positions as initial centroids for scikit-learn KMeans clustering.

## [0.2.15] - 2026-01-20

### Added
- Playwright browser integration tests for `SortableList` widget, verifying full browser-to-Python round-trip communication. Tests cover rendering, adding/removing/editing items, and Python state synchronization.
- New `test-browser` optional dependency group and CI workflow for running browser tests with marimo.

### Removed
- Removed unused `pydantic-ai` dependency that was pulling in `openai` and breaking WASM demos.

## [0.2.14] - 2026-01-19

### Fixed
- `EnvConfig` now displays values in input fields even when validation fails, so users can see what was loaded or entered rather than an empty field.
- Removed footer color changes in `EnvConfig`. Individual row highlighting (green/red) is now the sole status indicator, making the UI more consistent.

## [0.2.13] - 2026-01-15

### Added
- New `EnvConfig` widget for environment variable configuration with validation. Displays a form UI for setting API keys with password-style masking, optional validator callbacks, and a `require_valid()` method to block execution until all variables are configured.

## [0.2.12] - 2026-01-12

### Added
- New `TextCompare` widget for side-by-side text comparison with match highlighting. Useful for plagiarism detection or finding shared passages between documents. Features hover-based highlighting that syncs between panels, configurable minimum match length via `min_match_words`, and programmatic access to detected matches.

## [0.2.11] - 2026-01-08

### Added
- New `PulsarChart` widget for stacked waveform visualization, inspired by the iconic PSR B1919+21 pulsar visualization from Joy Division's "Unknown Pleasures" album cover. Features include clickable rows with selection state synced back to Python, customizable overlap, stroke width, fill opacity, and peak scale.

## [0.2.10] - 2026-01-07

### Fixed
- Fixed "Maximum call stack size exceeded" error when rendering `Slider2D` widget on latest marimo. The widget had an infinite loop where model change handlers would trigger redraws that updated the model again.
