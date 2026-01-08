# HTMLRefreshWidget API


 Bases: `AnyWidget`


A widget that displays HTML content and refreshes when it changes.


This widget creates a div element that automatically updates whenever the `html` attribute is modified, making it ideal for displaying dynamically generated HTML content like SVG charts in Jupyter notebooks.



| Name | Type | Description |
| --- | --- | --- |
| `html` | `str` | The HTML content to display. |


Example:


```
import time
from wigglystuff import HTMLRefreshWidget

widget = HTMLRefreshWidget(html="<p>Hello!</p>")
display(widget)

# Update the widget with dynamic content
for i in range(10):
    widget.html = f"<p>Count: {i}</p>"
    time.sleep(0.5)
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `html` | `str` | The HTML content to display. |
