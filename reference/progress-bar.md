# ProgressBar API


 Bases: `AnyWidget`


A customizable progress bar widget for notebooks.


This widget displays a visual progress bar that updates in real-time as the `value` attribute changes.


One of the main benefits of this utility is that you have a progress bar that doesn't depend on ipywidgets while you still have something that works across notebook projects.



| Name | Type | Description |
| --- | --- | --- |
| `value` | `int` | The current progress value. Defaults to 0. |
| `max_value` | `int` | The maximum value representing 100% completion. Defaults to 100. |
| `color` | `str` | The fill color of the progress bar. Defaults to '#22c55e'. |
| `show_text` | `bool` | Whether to show the progress text below the bar. Defaults to True. |
| `width` | `str` | The CSS width of the progress bar. Defaults to '100%'. |
| `height` | `int` | The height of the bar in pixels. Defaults to 24. |


Example:


```
import time
from wigglystuff import ProgressBar

progress = ProgressBar(value=0, max_value=100)

for i in range(101):
    progress.value = i
    time.sleep(0.1)
```

 Source code in `wigglystuff/html.py`

```
def __init__(self, value: int = 0, max_value: int = 100, color: str = '#22c55e', show_text: bool = True, width: str = '100%', height: int = 24):
    super().__init__()
    self.value = value
    self.max_value = max_value
    self.color = color
    self.show_text = show_text
    self.width = width
    self.height = height
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int` | The current progress value. Defaults to 0. |
| `max_value` | `int` | The maximum value representing 100% completion. Defaults to 100. |
