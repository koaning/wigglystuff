# Changelog

All notable changes to this project will be documented in this file.

## [0.2.10] - 2026-01-07

### Fixed
- Fixed "Maximum call stack size exceeded" error when rendering `Slider2D` widget on latest marimo. The widget had an infinite loop where model change handlers would trigger redraws that updated the model again.
