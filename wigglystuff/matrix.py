from pathlib import Path
from typing import Any, List, Optional

import anywidget
import numpy as np
import traitlets


class Matrix(anywidget.AnyWidget):
    """Spreadsheet-like numeric editor with bounds, naming, and symmetry helpers.

    Examples:
        ```python
        matrix = Matrix(rows=3, cols=3, min_value=0, max_value=10)
        matrix
        ```
    """

    _esm = Path(__file__).parent / "static" / "matrix.js"
    _css = Path(__file__).parent / "static" / "matrix.css"
    matrix = traitlets.List([]).tag(sync=True)
    rows = traitlets.Int(3).tag(sync=True)
    cols = traitlets.Int(3).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    mirror = traitlets.Bool(False).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    digits = traitlets.Int(1).tag(sync=True)
    row_names = traitlets.List([]).tag(sync=True)
    col_names = traitlets.List([]).tag(sync=True)
    static = traitlets.Bool(False).tag(sync=True)
    flexible_cols = traitlets.Bool(False).tag(sync=True)

    def __init__(
        self,
        matrix: Optional[List[List[float]]] = None,
        rows: int = 3,
        cols: int = 3,
        min_value: float = -100,
        max_value: float = 100,
        triangular: bool = False,
        row_names: Optional[List[str]] = None,
        col_names: Optional[List[str]] = None,
        static: bool = False,
        flexible_cols: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create a Matrix editor.

        Args:
            matrix: Optional 2D list of initial values.
            rows: Number of rows when ``matrix`` is omitted.
            cols: Number of columns when ``matrix`` is omitted.
            min_value: Lower bound for cell values.
            max_value: Upper bound for cell values.
            triangular: If ``True``, enforce triangular editing constraints.
            row_names: Custom labels for rows.
            col_names: Custom labels for columns.
            static: Disable editing when ``True``.
            flexible_cols: Allow column count changes interactively.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if matrix is not None:
            matrix_array = np.array(matrix)
            if matrix_array.min() < min_value:
                raise ValueError(
                    f"The min value of input matrix is less than min_value={min_value}."
                )
            if matrix_array.max() > max_value:
                raise ValueError(
                    f"The max value of input matrix is less than max_value={max_value}."
                )
            rows, cols = matrix_array.shape
            matrix = matrix_array.tolist()
        else:
            matrix = [
                [(min_value + max_value) / 2 for _ in range(cols)]
                for _ in range(rows)
            ]

        if row_names is not None and len(row_names) != rows:
            raise ValueError(
                f"Length of row_names ({len(row_names)}) must match number of rows ({rows})."
            )
        if col_names is not None and len(col_names) != cols:
            raise ValueError(
                f"Length of col_names ({len(col_names)}) must match number of columns ({cols})."
            )

        if row_names is None:
            row_names = []
        if col_names is None:
            col_names = []

        super().__init__(
            matrix=matrix,
            rows=rows,
            cols=cols,
            min_value=min_value,
            max_value=max_value,
            triangular=triangular,
            row_names=row_names,
            col_names=col_names,
            static=static,
            flexible_cols=flexible_cols,
            **kwargs,
        )
