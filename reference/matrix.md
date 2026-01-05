# Matrix API


 Bases: `AnyWidget`


Spreadsheet-like numeric editor with bounds, naming, and symmetry helpers.


Examples:


```
matrix = Matrix(rows=3, cols=3, min_value=0, max_value=10)
matrix
```


Create a Matrix editor.


Parameters:


**

**

**

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `matrix` | `Optional[List[List[float]]]` | Optional 2D list of initial values. | `None` |
| `rows` | `int` | Number of rows when `matrix` is omitted. | `3` |
| `cols` | `int` | Number of columns when `matrix` is omitted. | `3` |
| `min_value` | `float` | Lower bound for cell values. | `-100` |
| `max_value` | `float` | Upper bound for cell values. | `100` |
| `triangular` | `bool` | If `True`, enforce triangular editing constraints. | `False` |
| `row_names` | `Optional[List[str]]` | Custom labels for rows. | `None` |
| `col_names` | `Optional[List[str]]` | Custom labels for columns. | `None` |
| `static` | `bool` | Disable editing when `True`. | `False` |
| `flexible_cols` | `bool` | Allow column count changes interactively. | `False` |
| `step` |  | Increment step size for cell value adjustments (via `**kwargs`). | required |
| `digits` |  | Number of decimal digits to display (via `**kwargs`). | required |
| `mirror` |  | If `True`, mirror edits symmetrically across the diagonal (via `**kwargs`). | required |
| `**kwargs` | `Any` | Forwarded to `anywidget.AnyWidget`. | `{}` |

 Source code in `wigglystuff/matrix.py`

```
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
        step: Increment step size for cell value adjustments (via ``**kwargs``).
        digits: Number of decimal digits to display (via ``**kwargs``).
        mirror: If ``True``, mirror edits symmetrically across the diagonal (via ``**kwargs``).
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
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `matrix` | `list[list[float]]` | Cell values. |
| `rows` | `int` | Row count. |
| `cols` | `int` | Column count. |
| `min_value` | `float` | Minimum allowed value. |
| `max_value` | `float` | Maximum allowed value. |
| `mirror` | `bool` | Mirror edits across the diagonal when enabled. |
| `step` | `float` | Step size for edits. |
| `digits` | `int` | Decimal precision for display. |
| `row_names` | `list[str]` | Optional row labels. |
| `col_names` | `list[str]` | Optional column labels. |
| `static` | `bool` | Disable editing when true. |
| `flexible_cols` | `bool` | Allow column count changes interactively. |
