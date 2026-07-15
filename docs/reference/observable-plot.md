# ObservablePlot API

::: wigglystuff.observable_plot.ObservablePlot

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Resolved Observable Plot JavaScript (inline JS, or the contents of a file / URL, fetched in Python), evaluated as an expression that returns the DOM node to mount. |
| `variables` | `dict` | Name → value mapping injected into the code's scope as JavaScript variables. DataFrames and numpy arrays are converted to JSON records/lists on assignment. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
| `version` | `str` | `@observablehq/plot` version loaded from the CDN (defaults to `"latest"`). |
| `error` | `str` | Read-back of the latest JS runtime / CDN-load error, or `""`. |
