# ProgressBar API


 Bases: `AnyWidget`


A customizable progress bar widget for notebooks.


This widget displays a visual progress bar that updates in real-time as the `value` attribute changes. It shows both a graphical representation and a numerical indicator (percentage and fraction).


One of the main benefits of this utility is that you have a progress bar that doesn't depend on ipywidgets while you still have something that works across notebook projects.


Attributes:


| Name | Type | Description |
| --- | --- | --- |
| `value` | `int` | The current progress value. Defaults to 0. |
| `max_value` | `int` | The maximum value representing 100% completion. Defaults to 100. |


Example:


```
import time
from wigglystuff import ProgressBar

progress = ProgressBar(value=0, max_value=100)
display(progress)

for i in range(101):
    progress.value = i
    time.sleep(0.1)
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int` | The current progress value. Defaults to 0. |
| `max_value` | `int` | The maximum value representing 100% completion. Defaults to 100. |
