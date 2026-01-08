# Changelog

All notable changes to this project will be documented in this file.

## [0.2.11] - 2026-01-08

### Added
- New `PulsarChart` widget for stacked waveform visualization, inspired by the iconic PSR B1919+21 pulsar visualization from Joy Division's "Unknown Pleasures" album cover. Features include clickable rows with selection state synced back to Python, customizable overlap, stroke width, fill opacity, and peak scale.

## [0.2.10] - 2026-01-07

### Fixed
- Fixed "Maximum call stack size exceeded" error when rendering `Slider2D` widget on latest marimo. The widget had an infinite loop where model change handlers would trigger redraws that updated the model again.
