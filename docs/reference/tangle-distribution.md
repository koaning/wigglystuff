---
title: "TangleDistribution: drag a whole distribution inline"
description: TangleDistribution is a Tangle-style inline control that holds a probability distribution. Drag left/right and up/down to change its two parameters, watch a live preview of the shape, and read cdf, ppf, pdf/pmf and samples back in Python.
---

# TangleDistribution API

Try it live: [open the demo notebook in molab](https://molab.marimo.io/github/koaning/wigglystuff/blob/main/demos/tangle_distribution.py/wasm?utm_source=wigglystuff).

Sometimes a single number is too confident. `TangleDistribution` puts a whole
distribution inside your prose, rendered as `50.0 ± 10.0` by default. Drag
left/right to change one parameter and up/down to change the other; while you
drag, a small chart floats above the page with the starting shape dashed and the
current one filled, so you can see exactly what you are changing.

Fourteen families are supported (`TangleDistribution.distributions`), named after
their `scipy.stats` counterparts and using the same parameters. The maths is built
in, so `cdf`, `ppf`, `pdf`/`pmf` and `sample` work without scipy, and only for the
families listed here.

| family | kind | ↔ drag | ↕ drag |
| --- | --- | --- | --- |
| `norm` | continuous | `loc` | `scale` |
| `lognorm` | continuous | `scale` (the median) | `s` |
| `gamma` | continuous | `scale` | `a` (the shape) |
| `expon` | continuous | `scale` (the mean) | (none) |
| `weibull_min` | continuous | `scale` | `c` (the shape) |
| `uniform` | continuous | `loc` (left edge) | `scale` (width) |
| `laplace` | continuous | `loc` | `scale` |
| `logistic` | continuous | `loc` | `scale` |
| `beta` | continuous | `a` | `b` |
| `poisson` | discrete | `mu` | (none) |
| `binom` | discrete | `p` | `n` (whole number) |
| `nbinom` | discrete | `p` | `n` |
| `geom` | discrete | `p` | (none) |
| `randint` | discrete | `low` | `high` (excluded, as in scipy) |

`params` only changes when you let go of a drag. While dragging, `live_params`
follows the pointer and `dragging` is `True`, so the rest of a notebook can show
the old and the new distribution side by side. Every method takes `live=True` to
use the in-progress values:

```python
from wigglystuff import TangleDistribution

delivery = TangleDistribution("lognorm", params={"scale": 25, "s": 0.3}, template="{mean:.0f} ± {sd:.0f} minutes")

delivery.ppf(0.9)            # 90% of deliveries arrive within this many minutes
delivery.cdf(30)             # chance it arrives within half an hour
delivery.sample(1000)        # numpy array of draws
delivery.ppf(0.9, live=True) # the same, for the distribution being dragged right now
```

The inline text comes from `template`. Its placeholders are the keys of `params`
plus the computed `mean` and `sd` (`widget.template_fields` lists them), each with
an optional `:.Nf` precision, e.g. `"median {scale:.0f} days (s={s:.2f})"`.

See also: [Tangle widgets](tangle.md) for a single draggable number, and
[TangleFunction](tangle-function.md) for turning a whole function call into
draggable arguments.

::: wigglystuff.tangle.TangleDistribution

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `distribution` | `str` | Family name, one of `TangleDistribution.distributions`. |
| `params` | `dict` | Committed parameters by scipy name; changes when a drag is released. |
| `live_params` | `dict` | In-progress parameters while dragging; equals `params` otherwise. |
| `dragging` | `bool` | `True` while the pointer is held down on the widget. |
| `bounds` | `dict` | `[low, high]` per parameter; either end may be `None`. |
| `steps` | `dict` | Change per drag step, per parameter. |
| `pixels_per_step` | `int` | Drag distance per step. |
| `template` | `str` | Inline text with `{param}`, `{mean}` and `{sd}` placeholders. |
| `digits` | `int` | Default number of decimals in the inline text. |
| `sync_throttle_ms` | `int` | Cap on how often `live_params` reaches Python while dragging. |
