from pathlib import Path
import anywidget
import traitlets


class Slider2D(anywidget.AnyWidget):
    """
    A scatter drawing widget that automatically can update a pandas/polars dataframe
    as your draw data.
    """
    _esm = Path(__file__).parent / 'static' / '2dslider.js'
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)


class Matrix(anywidget.AnyWidget):
    """
    A very small excel experience for some quick number entry
    """
    _esm = Path(__file__).parent / 'static' / 'matrix.js'
    _css = Path(__file__).parent / 'static' / 'matrix.css'
    matrix = traitlets.List([]).tag(sync=True)
    rows = traitlets.Int(3).tag(sync=True)
    cols = traitlets.Int(3).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    mirror = traitlets.Bool(False).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)

    def __init__(self, matrix=None, rows=3, cols=3, min_value=-100, max_value=100, mirror=False, step=1.0):
        if matrix is not None:
            import numpy as np
            matrix = np.array(matrix)
            if matrix.min() < min_value:
                raise ValueError(f"The min value of input matrix is less than min_value={min_value}.")
            if matrix.max() > max_value:
                raise ValueError(f"The max value of input matrix is less than max_value={max_value}.")
            rows, cols = matrix.shape
            matrix = matrix.tolist()
        else:
            matrix = [[(min_value + max_value) / 2 for i in range(cols)] for j in range(rows)]
        super().__init__(
            matrix=matrix, 
            rows=rows, 
            cols=cols, 
            mirror=mirror, 
            min_value=min_value, 
            max_value=max_value, 
            step=step,
        )
