# PulsarChart API


 Bases: `AnyWidget`


Stacked overlapping line charts creating a ridge/horizon effect.


Inspired by the iconic PSR B1919+21 pulsar visualization from Joy Division's "Unknown Pleasures" album cover. Each row represents a waveform that can overlap with adjacent rows.



```
from wigglystuff import PulsarChart

import pandas as pd
import numpy as np

# Generate sample waveform data
n_rows = 40
n_points = 100
data = {}
for i in range(n_points):
    col = []
    for j in range(n_rows):
        x = i / n_points * 4 * np.pi
        y = np.sin(x + j * 0.1) * np.random.uniform(0.5, 1.5)
        col.append(y)
    data[i] = col

df = pd.DataFrame(data)
df.index = range(10, 10 + n_rows)  # Custom index

chart = PulsarChart(df, x_label="Time", y_label="Channel")
chart
```


Create a PulsarChart widget.


  Source code in `wigglystuff/pulsar_chart.py`

```
def __init__(
    self,
    df: Any,
    width: int = 600,
    height: int = 400,
    overlap: float = 0.5,
    stroke_width: float = 1.5,
    fill_opacity: float = 1.0,
    peak_scale: float = 1.0,
    x_label: str = "",
    y_label: str = "",
    **kwargs: Any,
) -> None:
    """Create a PulsarChart widget.

    Args:
        df: A pandas or polars DataFrame where each row is a waveform.
            The DataFrame index will be used as row labels on the y-axis.
        width: Chart width in pixels.
        height: Chart height in pixels.
        overlap: Amount of vertical overlap between rows (0.0 to 1.0).
        stroke_width: Line stroke width in pixels.
        fill_opacity: Opacity of the fill beneath each line (0.0 to 1.0).
        peak_scale: Multiplier for peak height (1.0 = default, 2.0 = double height).
        x_label: Label for the x-axis.
        y_label: Label for the y-axis.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    data, x_values = self._convert_dataframe(df)

    super().__init__(
        data=data,
        x_values=x_values,
        width=width,
        height=height,
        overlap=overlap,
        stroke_width=stroke_width,
        fill_opacity=fill_opacity,
        peak_scale=peak_scale,
        x_label=x_label,
        y_label=y_label,
        **kwargs,
    )
```


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
