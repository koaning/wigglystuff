# ScatterWidget API


**Note:** `ScatterWidget` is provided by the `drawdata` package and re-exported here for convenience. You can use it via `from wigglystuff import ScatterWidget` or `from drawdata import ScatterWidget`.


 Bases: `AnyWidget`


Interactive scatter drawing widget for painting multi-class 2D data points.


The widget renders a D3-powered SVG canvas where you can paint data points using a configurable brush. Points are grouped by class (color) and batch, making it easy to generate labeled 2D datasets interactively.



```
from wigglystuff import ScatterWidget

from wigglystuff import ScatterWidget

widget = ScatterWidget(n_classes=3)
widget
```


Create a ScatterWidget.




**

| Type | Description |
| --- | --- |
| `ValueError` | If n_classes is not between 1 and 4. |

 Source code in `wigglystuff/scatter_widget.py`

```
def __init__(
    self,
    *,
    n_classes: int = 4,
    brushsize: int = 40,
    width: int = 800,
    height: int = 400,
    **kwargs: Any,
) -> None:
    """Create a ScatterWidget.

    Args:
        n_classes: Number of point classes (1-4). Each class gets a
            distinct color and label.
        brushsize: Initial brush radius in pixels.
        width: SVG viewBox width in pixels.
        height: SVG viewBox height in pixels.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.

    Raises:
        ValueError: If *n_classes* is not between 1 and 4.
    """
    if not 1 <= n_classes <= 4:
        raise ValueError("n_classes must be between 1 and 4")
    super().__init__(
        n_classes=n_classes,
        brushsize=brushsize,
        width=width,
        height=height,
        **kwargs,
    )
```


## data_as_X_y `property`


```
data_as_X_y
```


Return the drawn points as a `(X, y)` tuple of numpy arrays.


When configured with `n_classes=1` (regression scenario), returns `X` with shape `(n, 1)` containing `x` values and `y` as the target array.


When configured with `n_classes>1` (classification scenario), returns `X` with shape `(n, 2)` containing `(x, y)` coordinates and `y` as a list of color strings.


## data_as_pandas `property`


```
data_as_pandas
```


Return the drawn points as a :class:`pandas.DataFrame`.


Columns: `x`, `y`, `color`, `label`, `batch`.


## data_as_polars `property`


```
data_as_polars
```


Return the drawn points as a :class:`polars.DataFrame`.


Columns: `x`, `y`, `color`, `label`, `batch`.


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | List of drawn points with `x`, `y`, `color`, `label`, `batch` keys. |
| `brushsize` | `int` | Brush radius in pixels (default: 40). |
| `width` | `int` | SVG viewBox width in pixels (default: 800). |
| `height` | `int` | SVG viewBox height in pixels (default: 400). |
| `n_classes` | `int` | Number of point classes, 1-4 (default: 4). |
