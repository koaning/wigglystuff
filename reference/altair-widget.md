# AltairWidget API


 Bases: `AnyWidget`


Flicker-free Altair chart widget.


Wraps an Altair chart and uses the Vega View API to update data in-place when only the data portion of the spec changes, avoiding full DOM rebuilds.


The widget should be created once and then updated via the `chart` setter from a reactive cell. This keeps the DOM element stable and allows the JavaScript side to detect data-only changes and apply them smoothly.



```
from wigglystuff import AltairWidget

import altair as alt
import pandas as pd
from wigglystuff import AltairWidget

df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
chart = alt.Chart(df).mark_point().encode(x="x", y="y")
widget = AltairWidget(chart)
widget
```


Create an AltairWidget.


  Source code in `wigglystuff/altair_widget.py`

```
def __init__(
    self,
    chart: Any = None,
    *,
    width: int = 600,
    height: int = 400,
    **kwargs: Any,
) -> None:
    """Create an AltairWidget.

    Args:
        chart: An Altair chart object or a Vega-Lite spec dict. If ``None``,
            the widget starts empty and can be populated later via the
            ``chart`` setter.
        width: Container width in pixels.
        height: Container height in pixels.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    spec = {}
    if chart is not None:
        spec = self._chart_to_spec(chart)
    super().__init__(
        spec=spec,
        width=width,
        height=height,
        **kwargs,
    )
```


## chart `property` `writable`


```
chart
```


Write-only convenience property. Read `widget.spec` instead.


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `spec` | `dict` | Full Vega-Lite spec (from `chart.to_dict()`). |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
