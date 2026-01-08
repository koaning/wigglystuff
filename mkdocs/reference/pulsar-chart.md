# PulsarChart API

::: wigglystuff.pulsar_chart.PulsarChart

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list` | Internal data representation: list of {index, values} dicts. |
| `x_values` | `list` | X-coordinates (column names from DataFrame). |
| `width` | `int` | Chart width in pixels. |
| `height` | `int` | Chart height in pixels. |
| `overlap` | `float` | Amount of vertical overlap between rows (0.0 to 1.0). |
| `stroke_width` | `float` | Line stroke width in pixels. |
| `fill_opacity` | `float` | Opacity of the fill beneath each line (0.0 to 1.0). |
| `peak_scale` | `float` | Multiplier for peak height. |
| `x_label` | `str` | Label for the x-axis. |
| `y_label` | `str` | Label for the y-axis. |
| `selected_index` | `Any` | The index of the currently selected row (synced back to Python). |
| `selected_row` | `list` | The values of the currently selected row (synced back to Python). |
