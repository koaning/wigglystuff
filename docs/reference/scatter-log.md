# ScatterLog API

::: wigglystuff.scatter_log.ScatterLog

## Usage

Create the widget once, display it, then append points from a separate reactive
cell. Pass `y=` for one series or use named keyword arguments to append several
series at the same x-coordinate.

```python
log = ScatterLog(x_label="step", y_label="score")
log.append(x=step, loss=loss, accuracy=accuracy)
```

`data` returns a copy of the accumulated points, `clear()` resets the plot, and
`max_points` bounds the retained history.

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `spec` | `dict` | Current Vega-Lite scatter specification. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
