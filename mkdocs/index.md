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

- [Slider2D](reference/slider2d.md) [(demo)](examples/slider2d/index.html) exposes `x` and `y` in real time for optimization, controls, or gamepads.
- [Matrix](reference/matrix.md) [(demo)](examples/matrix/index.html) toggles mirroring, clamps steps, and streams eigen-updates.
- [Paint](reference/paint.md) [(demo)](examples/paint/index.html) ships a PIL surface so you can remix doodles, annotate images, and hand data to multimodal LLMs.
- [EdgeDraw](reference/edge-draw.md) [(demo)](examples/edgedraw/index.html) manipulates graphs directly, surfacing adjacency data for algorithms.
- [SortableList](reference/sortable-list.md) [(demo)](examples/sortlist/index.html) is a UX-friendly list manager, with add/remove/edit support.
- [WebkitSpeechToTextWidget](reference/talk.md) [(demo)](examples/talk/index.html) brings speech control to notebooks with simple event hooks.

Each widget page embeds a marimo-powered html-wasm export and links back to the exact notebook that generated the demo, so you can open the original `.py` file and rerun it locally.
