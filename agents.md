# Agents

`wigglystuff` ships a small roster of AnyWidget "agents" that surface different
input modalities (sliders, speech, paint, etc.) across notebook runtimes. This
page is a quick lookup so you can see what exists and which traitlets each agent
syncs back to Python.

## Quick reference

| Agent | Module/Class | Core traitlets | One-liner |
| --- | --- | --- | --- |
| Slider2D | `wigglystuff.slider2d.Slider2D` | `x`, `y`, `x_bounds`, `y_bounds`, `width`, `height` | 2D pointer for coupled parameters |
| ChartPuck | `wigglystuff.chart_puck.ChartPuck` | `x`, `y`, `x_bounds`, `y_bounds`, `axes_pixel_bounds`, `width`, `height`, `chart_base64`, `puck_radius`, `puck_color` | Draggable puck overlay for matplotlib charts |
| Matrix | `wigglystuff.matrix.Matrix` | `matrix`, `rows`, `cols`, `min_value`, `max_value`, `step`, `mirror` | Spreadsheet-like numeric editor |
| TangleSlider | `wigglystuff.tangle.TangleSlider` | `amount`, `min_value`, `max_value`, `step`, `pixels_per_step` | Inline slider ala Bret Victor |
| TangleChoice | `wigglystuff.tangle.TangleChoice` | `choice`, `choices` | Inline toggle among labels |
| TangleSelect | `wigglystuff.tangle.TangleSelect` | `choice`, `choices` | Dropdown version of the above |
| SortableList | `wigglystuff.sortable_list.SortableList` | `value`, `addable`, `removable`, `editable`, `label` | Drag-and-drop ordering with optional CRUD |
| CopyToClipboard | `wigglystuff.copy_to_clipboard.CopyToClipboard` | `text_to_copy` | Copies the payload into the OS clipboard |
| ColorPicker | `wigglystuff.color_picker.ColorPicker` | `color` | Native color input with `rgb` helper |
| EdgeDraw | `wigglystuff.edge_draw.EdgeDraw` | `names`, `links`, `directed`, `width`, `height` | Sketch node/link diagrams and query adjacency |
| Paint | `wigglystuff.paint.Paint` | `base64`, `width`, `height`, `store_background` | MS-Paint-style canvas with PIL helpers |
| ThreeWidget | `wigglystuff.three_widget.ThreeWidget` | `data`, `width`, `height`, `show_grid`, `show_axes`, `dark_mode`, `axis_labels`, `animate_updates`, `animation_duration_ms` | 3D scatter plot for point clouds |
| WebcamCapture | `wigglystuff.webcam_capture.WebcamCapture` | `image_base64`, `capturing`, `interval_ms`, `facing_mode` | Webcam preview with snapshot capture |
| GamepadWidget | `wigglystuff.gamepad.GamepadWidget` | `axes`, `current_button_press`, `dpad_*`, `current_timestamp` | Streams browser Gamepad API events |
| KeystrokeWidget | `wigglystuff.keystroke.KeystrokeWidget` | `last_key` | Captures the latest keypress w/ modifiers |
| WebkitSpeechToTextWidget | `wigglystuff.talk.WebkitSpeechToTextWidget` | `transcript`, `listening`, `trigger_listen` | WebKit speech recognition bridge |
| DriverTour | `wigglystuff.driver_tour.DriverTour` | `steps`, `auto_start`, `show_progress`, `active`, `current_step` | Guided product tours via Driver.js |
| CellTour | `wigglystuff.cell_tour.CellTour` | `steps`, `auto_start`, `show_progress`, `active`, `current_step` | Simplified cell-based tours for marimo |
| TextCompare | `wigglystuff.text_compare.TextCompare` | `text_a`, `text_b`, `matches`, `selected_match`, `min_match_words` | Side-by-side text diff with match highlighting |
| EnvConfig | `wigglystuff.env_config.EnvConfig` | `variables`, `all_valid` | Environment variable config with validation |

## Patterns to remember

- All agents inherit from `anywidget.AnyWidget`, so `widget.observe(handler)`
  remains the standard way to react to state changes.
- Constructors tend to validate bounds, lengths, or choice counts; let the
  raised `ValueError/TraitError` guide you instead of duplicating the logic.
- Several widgets expose helper methods (e.g., `Paint.get_pil()`,
  `EdgeDraw.get_adjacency_matrix()`)—lean on those rather than re-implementing
  conversions.
- Check `wigglystuff/__init__.py` for the names that are re-exported at the
  package root so you can keep imports consistent.
- The repo standardizes on [`uv`](https://github.com/astral-sh/uv) for Python
  workflows (`uv pip install -e .` etc.) and the standard library's `pathlib`
  for filesystem paths—mirror those choices in new agents to keep the codebase
  consistent.
- When styling widgets, support both light and dark themes by defining
  component-specific CSS variables (see Matrix/SortableList). Scope your
  defaults to the widget root, mark `color-scheme: light dark`, and provide
  overrides that respond to `.dark`, `.dark-theme`, or `[data-theme="dark"]`
  ancestors so notebook-level theme toggles work instantly.
- When adding a new widget, remember to update the docs gallery
  (`mkdocs/index.md`), the README gallery (`readme.md`), and the LLM context
  file (`mkdocs/llms.txt`). Add a screenshot to `mkdocs/assets/gallery/` and
  reference it from the gallery locations to keep them in sync.
- Each widget has a demo marimo notebook in the `demos/` folder (e.g.,
  `demos/colorpicker.py`). When adding a new widget, create a corresponding
  demo notebook. Run demos with `marimo edit demos/<widget>.py`.
- **Always run `uv run marimo check demos/<notebook>.py`** after editing a demo
  notebook to verify it parses correctly and has no cell dependency issues.
- Dumber is better. Prefer obvious, direct code over clever abstractions—someone
  new to the project should be able to read the code top-to-bottom and grok it
  without needing to look up framework magic or trace through indirection.
