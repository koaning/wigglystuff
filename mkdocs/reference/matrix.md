# Matrix API

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `matrix` | `list[list[float]]` | Cell values. |
| `rows` | `int` | Row count. |
| `cols` | `int` | Column count. |
| `min_value` | `float` | Minimum allowed value. |
| `max_value` | `float` | Maximum allowed value. |
| `mirror` | `bool` | Mirror edits across the diagonal when enabled. |
| `step` | `float` | Step size for edits. |
| `digits` | `int` | Decimal precision for display. |
| `row_names` | `list[str]` | Optional row labels. |
| `col_names` | `list[str]` | Optional column labels. |
| `static` | `bool` | Disable editing when true. |
| `flexible_cols` | `bool` | Allow column count changes interactively. |

::: wigglystuff.matrix.Matrix
