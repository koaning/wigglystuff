# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "scikit-learn",
#     "wigglystuff==0.2.31",
# ]
# ///

import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.datasets import make_moons, make_blobs
    from wigglystuff import ChartMultiSelect

    COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    return COLORS, ChartMultiSelect, make_blobs, make_moons, mo, np


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ChartMultiSelect Demo

    Draw multiple box or lasso selections to classify points on a matplotlib chart.

    - Pick a **class** (a, b, ...) then draw regions with **Box** or **Lasso**
    - Click a selection to highlight it, then use the **delete** button to remove it
    - Use **undo** to remove the last-drawn selection
    - Use **clear** to remove all selections
    """)
    return


@app.cell
def _(make_moons, np):
    X_moons, y_moons = make_moons(n_samples=300, noise=0.15, random_state=42)
    x_moons = X_moons[:, 0]
    y_moons_coord = X_moons[:, 1]
    # Shift so the two moons are nicely centered
    pad = 0.5
    x_lo, x_hi = float(np.min(x_moons) - pad), float(np.max(x_moons) + pad)
    y_lo, y_hi = float(np.min(y_moons_coord) - pad), float(np.max(y_moons_coord) + pad)
    return x_hi, x_lo, x_moons, y_hi, y_lo, y_moons, y_moons_coord


@app.cell
def _(
    COLORS,
    ChartMultiSelect,
    x_hi,
    x_lo,
    x_moons,
    y_hi,
    y_lo,
    y_moons,
    y_moons_coord,
):
    def draw_moons(ax, widget):
        for c in range(2):
            mask = y_moons == c
            ax.scatter(
                x_moons[mask], y_moons_coord[mask],
                alpha=0.6, color=COLORS[c], s=20, label=f"Class {c}",
            )
        ax.legend(fontsize=8)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, alpha=0.3)
        ax.set_title("Draw selections to classify the two moons")

    ms = ChartMultiSelect.from_callback(
        draw_fn=draw_moons,
        x_bounds=(x_lo, x_hi),
        y_bounds=(y_lo, y_hi),
        figsize=(6, 4),
        n_classes=2,
        mode="lasso",
    )
    return (ms,)


@app.cell
def _(mo, ms):
    widget = mo.ui.anywidget(ms)
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, np, widget, x_moons, y_moons, y_moons_coord):
    _labels = widget.get_labels(x_moons, y_moons_coord)
    _classified = _labels >= 0
    _msg = "Draw selections to classify points, then check accuracy here."
    if _classified.any():
        _correct = int(np.sum(_labels[_classified] == y_moons[_classified]))
        _total = int(_classified.sum())
        _acc = _correct / _total * 100
        _msg = f"Accuracy on selected points: {_correct}/{_total} ({_acc:.1f}%)"
    mo.callout(_msg)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Three-Class Blobs

    Using `n_classes=3` with sklearn blobs — try to separate all three clusters.
    """)
    return


@app.cell
def _(make_blobs, np):
    X_blobs, y_blobs = make_blobs(
        n_samples=300, centers=3, cluster_std=0.8, random_state=7,
    )
    x_blobs = X_blobs[:, 0]
    y_blobs_coord = X_blobs[:, 1]
    pad3 = 1.0
    x3_lo, x3_hi = float(np.min(x_blobs) - pad3), float(np.max(x_blobs) + pad3)
    y3_lo, y3_hi = float(np.min(y_blobs_coord) - pad3), float(np.max(y_blobs_coord) + pad3)
    return x3_hi, x3_lo, x_blobs, y3_hi, y3_lo, y_blobs, y_blobs_coord


@app.cell(hide_code=True)
def _(
    COLORS,
    ChartMultiSelect,
    x3_hi,
    x3_lo,
    x_blobs,
    y3_hi,
    y3_lo,
    y_blobs,
    y_blobs_coord,
):
    def draw_blobs(ax, widget):
        for c in range(3):
            mask = y_blobs == c
            ax.scatter(
                x_blobs[mask], y_blobs_coord[mask],
                alpha=0.6, color=COLORS[c], s=20, label=f"Class {c}",
            )
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_title("Draw selections to classify the three blobs")

    ms3 = ChartMultiSelect.from_callback(
        draw_fn=draw_blobs,
        x_bounds=(x3_lo, x3_hi),
        y_bounds=(y3_lo, y3_hi),
        figsize=(6, 5),
        n_classes=3,
        mode="box",
    )
    return (ms3,)


@app.cell
def _(mo, ms3):
    w3 = mo.ui.anywidget(ms3)
    return (w3,)


@app.cell
def _(w3):
    w3
    return


@app.cell
def _(mo, np, w3, x_blobs, y_blobs, y_blobs_coord):
    _labels = w3.get_labels(x_blobs, y_blobs_coord)
    _classified = _labels >= 0
    _msg = "Draw selections to classify points, then check accuracy here."
    if _classified.any():
        _correct = int(np.sum(_labels[_classified] == y_blobs[_classified]))
        _total = int(_classified.sum())
        _acc = _correct / _total * 100
        _msg = f"Accuracy on selected points: {_correct}/{_total} ({_acc:.1f}%)"
    mo.callout(_msg)
    return


if __name__ == "__main__":
    app.run()
