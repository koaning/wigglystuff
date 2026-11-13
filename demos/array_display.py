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

    from wigglystuff import array_display

    return array_display, mo, np


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Shape-only NumPy arrays

    `array_display` keeps the behavior of a NumPy array while replacing its
    marimo output with an abstract shape. Use a string for a dimension whose
    size does not matter to the story and `None` for a dimension that should
    show its current size.

    Pass `name=` to put a label above the shape: plain strings render in
    serif — a lone letter as an italic math variable, longer text upright —
    and TeX-flavored names (`$\mathbf{X}$`, `$W^{(1)}$`, `$\hat{\theta}$`,
    `$\mathcal{L}$`) render through a small LaTeX subset using Unicode — no
    renderer or dependency needed.
    """)
    return


@app.cell
def _(array_display, np):
    matrix = array_display(
        np.arange(256).reshape(128, 2),
        display_shape=("n", None),
        name=r"$\mathbf{X}$",
    )
    tensor = array_display(
        np.zeros((32, 8, 3)),
        display_shape=("batch", "n", None),
        name=r"$\mathbf{A}_{batch}$",
    )
    plain = array_display(np.zeros((64, 3)), name="logits")
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
    return arrays with the same shape-only presentation, and the name rides
    along with views and elementwise results. Arrays rebuilt from several
    inputs — like the `np.concatenate` below — drop it.
    """)
    return


@app.cell
def _(matrix, mo, np):
    shifted = matrix + 10
    joined = np.concatenate([matrix, shifted], axis=1)
    mo.hstack([shifted, joined], justify="center", gap=3)
    return


@app.cell(hide_code=True)
def _(matrix, mo):
    mo.md(f"""
    `matrix.value` is a plain **{type(matrix.value).__name__}** with "
        f"shape `{matrix.value.shape}`.
    """)
    return


if __name__ == "__main__":
    app.run()
