---
title: "AsyncFlow: visualize asyncio task timeline"
description: AsyncFlow traces one asyncio run in marimo and draws a live swimlane timeline of every task, showing what is running and what sits suspended at an await.
image: asyncflow
image_alt: AsyncFlow widget showing a swimlane timeline with one bar per async task
---

# AsyncFlow API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="asyncflow" data-demo-title="AsyncFlow live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/asyncflow.webp" alt="AsyncFlow widget showing a swimlane timeline with one bar per async task" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`AsyncFlow` runs a coroutine on the notebook's own event loop and streams its task
activity into a swimlane timeline that fills in as the run proceeds: one lane per task,
solid bars where a task is running, hatched bars where it sits suspended at an `await`,
indented under the parent that spawned it. You use it as
`flow = await AsyncFlow.trace(main())`, which displays the live widget and returns it
once the run finishes. Capture relies on `sys.monitoring`, so Python 3.12 or newer is
required.

See also: [LiveEdit](live-edit.md) for the same pass-by-pass reading of a synchronous
function, [ObservablePlot](observable-plot.md) for charting the timings you collect, and
[EsmWidget](esm-widget.md) for building your own timeline view in JavaScript.

::: wigglystuff.async_flow.AsyncFlow

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `events` | `list[dict]` | Captured event stream; re-synced on every poll tick so the timeline grows live. Each entry has `t_ms`, `coro`, `event`, `task`, `line`, `detail`. |
| `now_ms` | `float` | Elapsed wall-clock milliseconds; advances every tick so suspended bars keep growing during long sleeps. |
| `running` | `bool` | Whether a run is currently in flight. |
| `width` | `int` | Widget width in pixels; `0` grows to fit. |
