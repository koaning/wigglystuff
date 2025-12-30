# ImageRefreshWidget API


 Bases: `AnyWidget`


A widget that displays an image and refreshes when the source changes.


This widget creates an image element that automatically updates whenever the `src` attribute is modified, making it ideal for displaying dynamically generated images in Jupyter notebooks.


Attributes:


| Name | Type | Description |
| --- | --- | --- |
| `src` | `str` | The image source, typically a base64-encoded data URI. |


Example:


```
from wigglystuff import ImageRefreshWidget
from wigglystuff.utils import refresh_matplotlib
import matplotlib.pylab as plt
import numpy as np

@refresh_matplotlib
def plot_data(data):
    plt.plot(np.arange(len(data)), np.cumsum(data))

widget = ImageRefreshWidget(src=plot_data([1, 2, 3, 4]))
display(widget)

# Update the widget with new data
widget.src = plot_data([1, 2, 3, 4, 5, 6])
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `src` | `str` | The image source, typically a base64-encoded data URI. |
