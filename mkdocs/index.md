---
title: wigglystuff
hide:
  - toc
---

# Wiggly notebooks, zero friction

> "A collection of creative AnyWidgets for Python notebook environments."

## Install wigglystuff

=== "uv"

    ```bash
    uv pip install wigglystuff
    ```

=== "pip"

    ```bash
    pip install wigglystuff
    ```


## What you can build

- [Slider2D](examples/slider2d/index.html) [(API)](reference/slider2d.md) exposes `x` and `y` in real time for optimization, controls, or gamepads.
- [Matrix](examples/matrix/index.html) [(API)](reference/matrix.md) toggles mirroring, clamps steps, and streams eigen-updates.
- [Paint](examples/paint/index.html) [(API)](reference/paint.md) ships a PIL surface so you can remix doodles, annotate images, and hand data to multimodal LLMs.
- [EdgeDraw](examples/edgedraw/index.html) [(API)](reference/edge-draw.md) manipulates graphs directly, surfacing adjacency data for algorithms.
- [SortableList](examples/sortlist/index.html) [(API)](reference/sortable-list.md) is a UX-friendly list manager, with add/remove/edit support.
- [WebkitSpeechToTextWidget](examples/talk/index.html) [(API)](reference/talk.md) brings speech control to notebooks with simple event hooks.
- [KeystrokeWidget](examples/keystroke/index.html) [(API)](reference/keystroke.md) captures shortcuts with modifier metadata so you can wire notebook hotkeys.
- [GamepadWidget](examples/gamepad/index.html) [(API)](reference/gamepad.md) streams controller axes, d-pad directions, and button presses for playful control schemes.
- [ColorPicker](examples/colorpicker/index.html) [(API)](reference/color-picker.md) streams both hex and RGB values for live theming or palette capture.
- [CopyToClipboard](examples/copytoclipboard/index.html) [(API)](reference/copy-to-clipboard.md) offers a one-click button that copies any string payload to the OS clipboard.

Each widget page embeds a marimo-powered html-wasm export and links back to the exact notebook that generated the demo, so you can open the original `.py` file and rerun it locally.
