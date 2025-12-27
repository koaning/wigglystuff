# LatexFormula API

::: wigglystuff.latex_formula.LatexFormula

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `parts` | `list[str]` | List of LaTeX strings to render. Parts are rendered sequentially and can be chained together. |
| `font_size` | `float` | Font size in pixels for the formula. |
| `display_mode` | `bool` | If True, renders as a block (centered, larger spacing). If False, renders inline. |

## Examples

### Simple Formula

```python
from wigglystuff import LatexFormula

formula = LatexFormula(parts=["x^2 + y^2 = r^2"])
```

### Chained Parts

You can chain multiple parts together to build complex formulas:

```python
formula = LatexFormula(
    parts=[
        "A",
        "=",
        "\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}"
    ]
)
```

### Display Mode

Use display mode for centered, block-level formulas:

```python
formula = LatexFormula(
    parts=["\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}"],
    display_mode=True
)
```

### Integration with Matrix Widget

You can combine LaTeX formulas with Matrix widgets:

```python
from wigglystuff import LatexFormula, Matrix

matrix = Matrix(rows=2, cols=2)
formula = LatexFormula(
    parts=[
        "A",
        "=",
        "\\begin{pmatrix}",
        f"{matrix.matrix[0][0]:.2f}",
        "&",
        f"{matrix.matrix[0][1]:.2f}",
        "\\\\",
        f"{matrix.matrix[1][0]:.2f}",
        "&",
        f"{matrix.matrix[1][1]:.2f}",
        "\\end{pmatrix}"
    ]
)
```

### Dynamic Updates

You can update formula parts programmatically:

```python
formula = LatexFormula(parts=["f(x) = x^2"])

# Add a new part
formula.add_part(" + 2x + 1")

# Or replace all parts
formula.set_parts(["f(x) = x^3 + x"])
```
