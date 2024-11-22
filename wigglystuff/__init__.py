from typing import List
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
    rows = traitlets.Int(3).tag(sync=True)
    cols = traitlets.Int(3).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    triangular = traitlets.Bool(False).tag(sync=True)
    matrix = traitlets.List([]).tag(sync=True)

    def __init__(self, matrix=None, rows=3, cols=3, min_value=-100, max_value=100, triangular=False, **kwargs):
        # if triangular and (rows != cols):
        #     raise ValueError("triangular setting is only meant for square matrices")
        if matrix is not None:
            import numpy as np
            matrix = np.array(matrix)
            rows, cols = matrix.shape
            matrix = matrix.tolist()
        else:
            matrix = [[(min_value + max_value) / 2 for i in range(cols)] for j in range(rows)]
        super().__init__(matrix=matrix, rows=rows, cols=cols, triangular=triangular, **kwargs)


class TangleSlider(anywidget.AnyWidget):
    """
    A very small excel experience for some quick number entry
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-slider.js'
    amount = traitlets.Float(0.0).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    pixels_per_step = traitlets.Int(2).tag(sync=True)
    prefix = traitlets.Unicode("").tag(sync=True)
    suffix = traitlets.Unicode("").tag(sync=True)
    digits = traitlets.Int(1).tag(sync=True)

    def __init__(self, amount=None, min_value=-100, max_value=100, step=1.0, pixels_per_step=2, prefix="", suffix="", digits=1, **kwargs):
        if not amount:
            amount = (max_value + min_value)/2
        super().__init__(amount=amount, min_value=min_value, max_value=max_value, step=step, pixels_per_step=pixels_per_step, prefix=prefix, suffix=suffix, digits=digits, **kwargs)


class TangleChoice(anywidget.AnyWidget):
    """
    A UI element like tangle.js but for Python to make choices. 
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-choice.js'
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs):
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(value=choices[1], choices=choices, **kwargs)
