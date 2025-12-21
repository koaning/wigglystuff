# EdgeDraw API

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `names` | `list[str]` | Ordered node labels. |
| `links` | `list[dict]` | Link dicts with `source` and `target` keys. |
| `directed` | `bool` | Draw directed edges when true. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |

::: wigglystuff.edge_draw.EdgeDraw
