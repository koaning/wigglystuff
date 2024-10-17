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


class MiniExcel(anywidget.AnyWidget):
    """
    A very small excel experience for some quick number entry
    """
    _esm = Path(__file__).parent / 'static' / 'miniexcel.js'
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
    rows = traitlets.Int(3),
    cols = traitlets.Int(3),
    min_value = traitlets.Float(-100),
    max_value = traitlets.Float(100),
    triangular = traitlets.Bool(False).tag(sync=True)
