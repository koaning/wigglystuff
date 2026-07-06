# GridDraw API

::: wigglystuff.grid_draw.GridDraw

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `dots` | `list` | Drawn intersections as `[[row, col], ...]`. |
| `lines` | `list` | Drawn unit segments as `{"from": [r, c], "to": [r, c], "width": int}` dictionaries. |
| `rows` | `int` | Number of grid cells vertically; row intersections are `0..rows`. |
| `cols` | `int` | Number of grid cells horizontally; column intersections are `0..cols`. |
| `line_width` | `int \| list[int]` | Fixed line width, or picker options when a list is supplied. |
| `dot_radius` | `int` | Drawn dot radius in pixels. |
| `theme` | `str \| None` | `None` follows the notebook; `"light"` or `"dark"` forces the widget theme. |
| `width` | `int` | Widget width in pixels. |
| `height` | `int` | Widget height in pixels. |
