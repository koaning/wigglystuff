from typing import Any, List, Sequence
from pathlib import Path
import anywidget
import traitlets
import numpy as np


class Slider2D(anywidget.AnyWidget):
    """Initialize a Slider2D widget.

    Args:
        x: Initial x coordinate value. Defaults to 0.
        y: Initial y coordinate value. Defaults to 0.
        x_bounds: Tuple of min/max value for the x-axis. Defaults to (-1.0, 1.0).
        y_bounds: Tuple of min/max value for the y-axis. Defaults to (-1.0, 1.0).
        width: Width of the slider widget in pixels. Defaults to 400.
        height: Height of the slider widget in pixels. Defaults to 400.
        **kwargs: Additional keyword arguments passed to parent class.
    """
    _esm = Path(__file__).parent / 'static' / '2dslider.js'
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    x_bounds = traitlets.Tuple(traitlets.Float(), traitlets.Float(), default_value=(-1.0, 1.0)).tag(sync=True)
    y_bounds = traitlets.Tuple(traitlets.Float(), traitlets.Float(), default_value=(-1.0, 1.0)).tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)

    def __init__(
            self,
            x: float = 0.0,
            y: float = 0.0,
            width: int = 400,
            height: int = 400,
            x_bounds: tuple[float, float] = (-1.0, 1.0),
            y_bounds: tuple[float, float] = (-1.0, 1.0),
            **kwargs
        ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, x_bounds=x_bounds, y_bounds=y_bounds, **kwargs)

    @traitlets.validate("x_bounds", "y_bounds")
    def _valid_bounds(self, proposal: dict[str, Any]) -> tuple[float, float]:
        """Ensure min < max for bounds."""
        min_val, max_val = proposal["value"]
        if not (isinstance(min_val, float) and isinstance(max_val, float)):
                raise traitlets.TraitError("Bounds must be a tuple of two floats.")
        if min_val >= max_val:
            raise traitlets.TraitError("Min must be less than max in bounds.")
        return proposal["value"]

class Matrix(anywidget.AnyWidget):
    """Initialize a Matrix widget.

    Args:
        matrix: Optional 2D list of values to initialize the matrix with.
                If None, matrix will be initialized with mean of min/max values.
        rows: Number of rows in the matrix.
        cols: Number of columns in the matrix.
        min_value: Minimum allowed value in the matrix.
        max_value: Maximum allowed value in the matrix.
        triangular: If True, only allow editing upper triangle of matrix.
        row_names: Optional list of names for each row.
        col_names: Optional list of names for each column.
        static: If True, matrix is read-only and cannot be edited.
        flexible_cols: If True, columns expand to fit their content.
        **kwargs: Additional keyword arguments passed to parent class.
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
    row_names = traitlets.List([]).tag(sync=True)
    col_names = traitlets.List([]).tag(sync=True)
    static = traitlets.Bool(False).tag(sync=True)
    flexible_cols = traitlets.Bool(False).tag(sync=True)

    def __init__(self, matrix: List[List[float]] | None = None, 
                 rows: int = 3, 
                 cols: int = 3, 
                 min_value: float = -100, 
                 max_value: float = 100, 
                 triangular: bool = False,
                 row_names: List[str] | None = None,
                 col_names: List[str] | None = None,
                 static: bool = False,
                 flexible_cols: bool = False,
                 **kwargs) -> None:
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
        
        # Validate row_names and col_names dimensions
        if row_names is not None and len(row_names) != rows:
            raise ValueError(f"Length of row_names ({len(row_names)}) must match number of rows ({rows}).")
        if col_names is not None and len(col_names) != cols:
            raise ValueError(f"Length of col_names ({len(col_names)}) must match number of columns ({cols}).")
        
        # Set default empty lists if not provided
        if row_names is None:
            row_names = []
        if col_names is None:
            col_names = []
            
        super().__init__(matrix=matrix, rows=rows, cols=cols, min_value=min_value, 
                         max_value=max_value, triangular=triangular, row_names=row_names, 
                         col_names=col_names, static=static, flexible_cols=flexible_cols, **kwargs)


class TangleSlider(anywidget.AnyWidget):
    """Initialize a TangleSlider widget.

    Args:
        amount: Initial value of the slider. If None, uses mean of min/max.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        step: Step size for value changes.
        pixels_per_step: Number of pixels per step when dragging.
        prefix: Text to display before the value.
        suffix: Text to display after the value.
        digits: Number of decimal places to display.
        **kwargs: Additional keyword arguments passed to parent class.
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

    def __init__(self, 
                 amount: float | None = None,
                 min_value: float = -100,
                 max_value: float = 100,
                 step: float = 1.0,
                 pixels_per_step: int = 2,
                 prefix: str = "",
                 suffix: str = "",
                 digits: int = 1,
                 **kwargs) -> None:
        if amount is None:
            amount = (max_value + min_value)/2
        super().__init__(amount=amount, min_value=min_value, max_value=max_value, step=step, pixels_per_step=pixels_per_step, prefix=prefix, suffix=suffix, digits=digits, **kwargs)


class TangleChoice(anywidget.AnyWidget):
    """Initialize a TangleChoice widget.

    Args:
        choices: List of at least two string choices to select from.
        **kwargs: Additional keyword arguments passed to parent class.

    Raises:
        ValueError: If fewer than two choices are provided.
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-choice.js'
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs) -> None:
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(value=choices[1], choices=choices, **kwargs)


class EdgeDraw(anywidget.AnyWidget):
    """Initialize a EdgeDraw widget.

    Args:
        names: List of names for the nodes.
    """
    _esm = Path(__file__).parent / 'static' / 'edgedraw.js'
    _css = Path(__file__).parent / 'static' / 'edgedraw.css'
    names = traitlets.List([]).tag(sync=True)
    links = traitlets.List([]).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)

    def __init__(self, names: List[str], height: int = 400, width: int = 600) -> None:
        super().__init__(names=names, height=height, width=width)

    def get_adjacency_matrix(self, directed: bool = False) -> np.ndarray:
        """Create an adjacency matrix from links and node names.

        Args:
            directed (bool): To follow directed graph or not
        Returns:
            matrix (numpy.ndarray): Adjacency matrix representing the graph.
        """
        num_nodes = len(self.names)
        matrix = np.zeros((num_nodes, num_nodes))
        for nodes in self.links:
            src = self.names.index(nodes["source"])
            dst = self.names.index(nodes["target"])
            matrix[src][dst] = 1
            if not directed:
                matrix[dst][src] = 1
        return matrix

    def get_neighbors(self, node_name: str, directed: bool = False) -> List[str]:
        """Get neighbores of a node.

        Args:
            node_name (str): Name of the node to get neighbors for.
            directed (bool): To follow directed graph or not
        Returns:
            neighbors (list): List of connected nodes.
        """
        neighbors=[]
        for nodes in self.links:
            if nodes['source']==node_name:
                neighbors.append(nodes['target'])
            if not directed:
                if nodes['target']==node_name:
                    neighbors.append(nodes['source'])
        return neighbors


class TangleSelect(anywidget.AnyWidget):
    """Initialize a TangleSelect widget.

    Args:
        choices: List of at least two string choices to select from in a dropdown.
        **kwargs: Additional keyword arguments passed to parent class.

    Raises:
        ValueError: If fewer than two choices are provided.
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-select.js'
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs) -> None:
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(choice=choices[0], choices=choices, **kwargs)


class CopyToClipboard(anywidget.AnyWidget):
    """Initialize a CopyToClipboard widget.

    Args:
        text_to_copy: String to copy to the clipboard when button is pressed.
    """
    text_to_copy = traitlets.Unicode("").tag(sync=True)
    _esm = Path(__file__).parent / 'static' / 'copybutton.js'
    _css = Path(__file__).parent / 'static' / 'copybutton.css'

    def __init__(self, text_to_copy="", **kwargs):
        super().__init__(**kwargs)
        self.text_to_copy = text_to_copy


class ColorPicker(anywidget.AnyWidget):
    """Initialize a ColorPicker widget.

    Args:
        color: Hex code of color.
    """
    _esm = Path(__file__).parent/"static"/"colorpicker.js"
    color = traitlets.Unicode("#000000").tag(sync=True)

    def __init__(self, *, color=None, **kwargs):
        if color is not None:
            kwargs["color"] = color
        super().__init__(**kwargs)
    
    @property
    def rgb(self):
        return tuple(int(self.color[i:i+2], 16) for i in (1, 3, 5))


class SortableList(anywidget.AnyWidget):
    """Interactive sortable list with optional add, remove, and edit functionality.

    Args:
        value: List of string items to display
        addable: Enable adding new items via input field (default: False)
        removable: Enable removing items with [x] buttons (default: False)
        editable: Enable inline editing by clicking items (default: False)
    """

    _esm = Path(__file__).parent / "static" / "sortable-list.js"
    _css = Path(__file__).parent / "static" / "sortable-list.css"
    value = traitlets.List(traitlets.Unicode()).tag(sync=True)
    addable = traitlets.Bool(default_value=False).tag(sync=True)
    removable = traitlets.Bool(default_value=False).tag(sync=True)
    editable = traitlets.Bool(default_value=False).tag(sync=True)

    def __init__(
        self,
        value: Sequence[str],
        *,
        addable: bool = False,
        removable: bool = False,
        editable: bool = False,
    ) -> None:
        super().__init__(
            value=list(value), addable=addable, removable=removable, editable=editable
        )

