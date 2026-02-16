# ScatterWidget API

::: wigglystuff.scatter_widget.ScatterWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | List of drawn points with `x`, `y`, `color`, `label`, `batch` keys. |
| `brushsize` | `int` | Brush radius in pixels (default: 40). |
| `width` | `int` | SVG viewBox width in pixels (default: 800). |
| `height` | `int` | SVG viewBox height in pixels (default: 400). |
| `n_classes` | `int` | Number of point classes, 1-4 (default: 4). |
