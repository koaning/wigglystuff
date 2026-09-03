---
title: "ProgressBar: progress bar, no ipywidgets"
description: ProgressBar shows loop progress that updates in real time from Python without an ipywidgets dependency, so the same code works in Jupyter, marimo and Colab.
image: progressbar
image_alt: ProgressBar widget showing a filled bar at 100 percent with a 100 slash 100 readout above it
---

# ProgressBar API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="progressbar" data-demo-title="ProgressBar live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/progressbar.webp" alt="ProgressBar widget showing a filled bar at 100 percent with a 100 slash 100 readout above it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ProgressBar` draws a bar that fills as `value` climbs towards `max_value`, with a
`color`, `width`, `height` and an optional `value / max` readout underneath. The reason it
exists is that it does not depend on ipywidgets, so a loop that assigns `bar.value` reports
progress the same way in whatever notebook you happen to be running, and it follows the
surrounding light or dark theme.

See also: [HTMLRefreshWidget](html-refresh.md) for status text updated in place next to it,
[AnnotationWidget](annotation.md) for the labeling queue that bar is often counting, and
[PlaySlider](play-slider.md) when the value should be driven by the reader instead.

## Script mode: a rich terminal bar

The same `ProgressBar` works outside a notebook too. When the code runs as a
script — either a plain Python file or a marimo notebook run with
`uv run notebook.py` — and the optional [`rich`](https://github.com/Textualize/rich)
library is installed, each `bar.value` assignment is mirrored into a fancy
animated bar in the terminal: a spinner, a bar colored from `color`, a
percentage, an `M/N` count (shown when `show_text` is `True`) and a
time-remaining estimate. Because the value is applied as an absolute position,
the terminal bar moves backward too if `value` decreases.

marimo distinguishes these modes with `mo.app_meta().mode` (`"edit"`/`"run"` in
the browser, `"script"` on the command line), and `ProgressBar` keys off the
same signal — so one notebook shows the browser widget when edited and the rich
bar when executed. No changes to your loop are needed either way:

```python
import time
from wigglystuff import ProgressBar

bar = ProgressBar(max_value=50)
for i in range(51):
    bar.value = i
    time.sleep(0.05)
```

Install rich with `pip install rich`. If `rich` is not installed, or the code
runs inside a notebook editor, this behaves exactly as before — nothing extra is
rendered.

::: wigglystuff.html.ProgressBar

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int` | The current progress value. Defaults to 0. |
| `max_value` | `int` | The maximum value representing 100% completion. Defaults to 100. |
