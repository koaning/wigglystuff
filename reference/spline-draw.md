# SplineDraw API


 Bases: `AnyWidget`


Draw scatter points and see a spline curve fitted through them.


This widget is built on the same D3/SVG canvas as ScatterWidget. The spline is computed by a Python callback function. Pass any callable with signature `(x, y) -> (x_curve, y_curve)` where inputs and outputs are 1-D numpy arrays.



```
from wigglystuff import SplineDraw

from wigglystuff import SplineDraw
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import LinearRegression

pipe = make_pipeline(SplineTransformer(), LinearRegression())

def spline_fn(x, y):
    pipe.fit(x.reshape(-1, 1), y)
    x_curve = np.linspace(x.min(), x.max(), 200)
    return x_curve, pipe.predict(x_curve.reshape(-1, 1))

widget = SplineDraw(spline_fn=spline_fn)
widget
```


Create a SplineDraw widget.


  Source code in `wigglystuff/spline_draw.py`

```
def __init__(
    self,
    spline_fn: Callable,
    *,
    n_classes: int = 1,
    brushsize: int = 40,
    width: int = 600,
    height: int = 400,
    **kwargs: Any,
) -> None:
    """Create a SplineDraw widget.

    Args:
        spline_fn: A callable ``(x, y) -> (x_curve, y_curve)`` where
            inputs are 1-D numpy arrays of drawn point coordinates and
            outputs are 1-D numpy arrays defining the fitted curve.
        n_classes: Number of point classes (1-4). Defaults to 1.
        brushsize: Initial brush radius in pixels.
        width: SVG viewBox width in pixels.
        height: SVG viewBox height in pixels.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if not 1 <= n_classes <= 4:
        raise ValueError("n_classes must be between 1 and 4")
    self._spline_fn = spline_fn
    super().__init__(
        n_classes=n_classes,
        brushsize=brushsize,
        width=width,
        height=height,
        **kwargs,
    )
    self.observe(self._recompute_curve, names=["data"])
```


## curve_as_numpy `property`


```
curve_as_numpy: dict[str, tuple[ndarray, ndarray]]
```


Return fitted curves as a dict keyed by color.


Each value is an `(x_array, y_array)` tuple of numpy arrays. With a single class the dict has one entry.


## data_as_X_y `property`


```
data_as_X_y
```


Return the drawn points as a `(X, y)` tuple of numpy arrays.


With `n_classes=1` returns X of shape `(n, 1)` with x values and y as target. With `n_classes>1` returns X of shape `(n, 2)` and y as color strings.


## data_as_numpy `property`


```
data_as_numpy: tuple[ndarray, ndarray]
```


Return the drawn points as `(x_array, y_array)` numpy arrays.


## data_as_pandas `property`


```
data_as_pandas
```


Return the drawn points as a :class:`pandas.DataFrame`.


## data_as_polars `property`


```
data_as_polars
```


Return the drawn points as a :class:`polars.DataFrame`.


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list` | Drawn scatter points (list of dicts with `x`, `y`, `color`). |
| `curve` | `list` | Fitted curve data computed by the spline function. |
| `curve_error` | `str` | Error message from the last spline computation, or empty string on success. |
| `brushsize` | `int` | Brush radius in pixels. |
| `n_classes` | `int` | Number of point classes (1–4). |
| `width` | `int` | SVG viewBox width in pixels. |
| `height` | `int` | SVG viewBox height in pixels. |
