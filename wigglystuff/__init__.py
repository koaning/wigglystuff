from pathlib import Path
import anywidget
import traitlets


class Slider2D(anywidget.AnyWidget):
    """
    A scatter drawing widget that automatically can update a pandas/polars dataframe
    as your draw data.

    Parameters:

    x: float
        The x position of the slider
    y: float
        The y position of the slider
    min_x: float
        The minimum x position of the slider
    max_x: float
        The maximum x position of the slider
    min_y: float
        The minimum y position of the slider
    max_y: float
        The maximum y position of the slider
    width: int
        The width of the slider
    height: int
        The height of the slider
    """
    _esm = Path(__file__).parent / 'static' / '2dslider.js'
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    min_x = traitlets.Float(-1.0).tag(sync=True)
    min_y = traitlets.Float(-1.0).tag(sync=True)
    max_x = traitlets.Float(1.0).tag(sync=True)
    max_y = traitlets.Float(1.0).tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)

    def __init__(self, x=0.0, y=0.0, min_x=-1.0, max_x=1.0, min_y=-1.0, max_y=1.0, width=300, height=300, **kwargs):
        super().__init__(x=x, y=y, min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y, width=width, height=height, **kwargs)


class Matrix(anywidget.AnyWidget):
    """
    A matrix drawing widget that automatically represents a numpy matrix.

    Parameters:
    matrix: list of lists or a numpy array
        The matrix to draw
    rows: int
        The number of rows in the matrix
    cols: int
        The number of columns in the matrix
    min_value: float
        The minimum value in the matrix
    max_value: float
        The maximum value in the matrix
    step: float
        The step size for the matrix
    triangular: bool
        Whether to draw a triangular matrix
    """
    _esm = Path(__file__).parent / 'static' / 'matrix.js'
    _css = Path(__file__).parent / 'static' / 'matrix.css'
    rows = traitlets.Int(3).tag(sync=True)
    cols = traitlets.Int(3).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    triangular = traitlets.Bool(False).tag(sync=True)
    matrix = traitlets.List([]).tag(sync=True)

    def __init__(self, matrix=None, rows=None, cols=None, min_value=-100, max_value=100, triangular=False, **kwargs):
        if matrix is not None:
            import numpy as np
            matrix = np.array(matrix)
            rows, cols = matrix.shape
            matrix = matrix.tolist()
            if rows is not None or cols is not None:
                raise ValueError("If matrix is provided, rows and cols must not be provided")
        else:
            if not rows or not cols:
                raise ValueError("Either matrix or rows and cols must be provided")
            matrix = [[(min_value + max_value) / 2 for i in range(cols)] for j in range(rows)]
        super().__init__(matrix=matrix, rows=rows, cols=cols, triangular=triangular, **kwargs)
