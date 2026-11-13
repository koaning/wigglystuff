# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "wigglystuff==0.5.40",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo
    import numpy as np

    # Prefer the local checkout so the demo works before the next release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import shape_display

    return mo, np, shape_display


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Shape-only NumPy arrays

    `shape_display` keeps the behavior of a NumPy array while replacing its
    marimo output with an abstract shape. Use a string for a dimension whose
    size does not matter to the story and `None` for a dimension that should
    show its current size.

    Pass `name=` to put a label above the shape: plain strings render in
    serif — a lone letter as an italic math variable, longer text upright —
    and TeX-flavored names (`$\mathbf{X}$`, `$W^{(1)}$`, `$\hat{\theta}$`,
    `$\mathcal{L}$`) render with the KaTeX that ships with marimo.
    """)
    return


@app.cell
def _(np, shape_display):
    matrix = shape_display(
        np.arange(256).reshape(128, 2),
        labels=("n", "d"),
        name=r"$\mathbf{X}$",
    )
    tensor = shape_display(
        np.zeros((32, 8, 3)),
        labels=("batch", "n", None),
        name=r"$\mathbf{A}_{batch}$",
    )
    plain = shape_display(np.zeros((64, 3)), name="logits")
    return matrix, plain, tensor


@app.cell(hide_code=True)
def _(matrix, mo, plain, tensor):
    mo.hstack([matrix, plain, tensor], justify="center", gap=3)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Operations preserve the display

    The result is still an ndarray subclass. Arithmetic and NumPy functions
    return arrays with the same shape-only presentation. An axis keeps its
    label only while it keeps its size, so the caption never lies: after
    `X @ W` the `d` axis is gone and the new one shows its live size.

    Names are inferred for `@` and transposes: `X @ W` is named **XW** and
    `X.T` is **X**ᵀ. Slices keep the name, other computed results drop it, and
    `.set_name(...)` gives any result a name without touching the original.
    """)
    return


@app.cell
def _(matrix, mo, np, shape_display):
    weights = shape_display(np.ones((2, 5)), labels=("d", None), name=r"$\mathbf{W}$")
    projected = (matrix @ weights)
    joined = np.concatenate([matrix, matrix + 10], axis=1)

    mo.hstack([weights, matrix, projected, matrix.T, joined, matrix.T @ matrix], justify="center", gap=3)
    return


@app.cell(hide_code=True)
def _(matrix, mo):
    mo.md(f"""
    `matrix.value` is a plain **{type(matrix.value).__name__}** with
    shape `{matrix.value.shape}`.
    """)
    return


if __name__ == "__main__":
    app.run()
