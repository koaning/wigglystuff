import marimo

__generated_with = "0.18.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import LatexFormula, Matrix
    return LatexFormula, Matrix, mo


@app.cell
def _(LatexFormula, mo):
    # Simple formula example
    simple_formula = LatexFormula(
        parts=["x^2 + y^2 = r^2"],
        font_size=20
    )
    
    mo.vstack([
        mo.md("### Simple LaTeX Formula"),
        simple_formula,
    ])
    return simple_formula,


@app.cell
def _(LatexFormula, mo):
    # Chained parts example
    chained_formula = LatexFormula(
        parts=[
            "A",
            "=",
            "\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}"
        ],
        font_size=18
    )
    
    mo.vstack([
        mo.md("### Chained Formula Parts"),
        chained_formula,
    ])
    return chained_formula,


@app.cell
def _(LatexFormula, Matrix, mo):
    # Integration with Matrix widget
    matrix = Matrix(rows=2, cols=2, min_value=-10, max_value=10, step=0.1)
    
    # Formula that references the matrix
    formula_with_matrix = LatexFormula(
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
        ],
        font_size=18
    )
    
    mo.vstack([
        mo.md("### Formula with Matrix Widget"),
        mo.md("Edit the matrix below and see the formula update:"),
        mo.hstack([matrix, formula_with_matrix]),
    ])
    return formula_with_matrix, matrix


@app.cell
def _(LatexFormula, mo):
    # Complex formula example
    complex_formula = LatexFormula(
        parts=[
            "\\int_{-\\infty}^{\\infty}",
            "e^{-x^2}",
            "dx",
            "=",
            "\\sqrt{\\pi}"
        ],
        font_size=20,
        display_mode=True
    )
    
    mo.vstack([
        mo.md("### Complex Formula (Display Mode)"),
        complex_formula,
    ])
    return complex_formula,


@app.cell
def _(LatexFormula, mo):
    # Multiple formulas chained together
    formula1 = LatexFormula(parts=["f(x) = x^2 + 2x + 1"], font_size=16)
    formula2 = LatexFormula(parts=["g(x) = \\sin(x)"], font_size=16)
    formula3 = LatexFormula(
        parts=["h(x) = f(x) \\cdot g(x)"],
        font_size=16
    )
    
    mo.vstack([
        mo.md("### Multiple Formulas"),
        formula1,
        mo.md("and"),
        formula2,
        mo.md("combine to form:"),
        formula3,
    ])
    return formula1, formula2, formula3


@app.cell
def _(LatexFormula, mo):
    # Dynamic formula example
    import numpy as np
    
    # Create a formula that can be updated
    dynamic_formula = LatexFormula(
        parts=[
            "\\sum_{i=1}^{n}",
            "x_i",
            "=",
            "0"
        ],
        font_size=18
    )
    
    # Example: Update formula based on some computation
    n = 5
    values = np.random.randn(n)
    sum_val = np.sum(values)
    
    dynamic_formula.set_parts([
        "\\sum_{i=1}^{" + str(n) + "}",
        "x_i",
        "=",
        f"{sum_val:.2f}"
    ])
    
    mo.vstack([
        mo.md("### Dynamic Formula"),
        mo.md(f"For n={n} random values:"),
        dynamic_formula,
    ])
    return dynamic_formula, n, sum_val, values


if __name__ == "__main__":
    app.run()
