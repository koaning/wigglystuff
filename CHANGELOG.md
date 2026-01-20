# Changelog

All notable changes to this project will be documented in this file.

## [0.2.14] - 2026-01-19

### Added
- Playwright browser integration tests for `SortableList` widget, verifying full browser-to-Python round-trip communication. Tests cover rendering, adding/removing/editing items, and Python state synchronization.
- New `test-browser` optional dependency group and CI workflow for running browser tests with marimo.

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
