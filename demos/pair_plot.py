# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "numpy",
#     "wigglystuff==0.5.41",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import marimo as mo
    import numpy as np
    from wigglystuff import PairPlot

    return PairPlot, mo, np


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # PairPlot

    A scatterplot matrix with linked box and lasso selection, built to handle a lot of
    rows. The data goes to the browser as binary float32 and stays in a Web
    Worker; WebGL draws a bounded sample of points per cell, but a lasso is
    checked against **every** row.

    - **Drag** inside any scatter cell to draw a box. The selected rows keep
      their cluster colour in every cell; everything else turns gray.
    - **Drag the selection** to move it (box or lasso); every cell and
      histogram follows live. Python only hears about it when you let go.
    - Switch to **Lasso** for a freehand outline instead.
    - **Keep** narrows the plot to the selected rows and **Exclude** drops
      them; the axes rescale to what is left and filters stack. **Reset**
      brings every row back.
    - The **diagonal** histograms are exact: the full data stays in the
      background and the selection stacks on top in cluster colours.
    - **Click** outside the box, double-click, or press **Clear** to clear.
      **Full / Lower** switches between the whole matrix and the lower triangle.
    """)
    return


@app.cell
def _(mo):
    n_rows = mo.ui.dropdown(
        {"20 thousand": 20_000, "200 thousand": 200_000, "1 million": 1_000_000},
        value="200 thousand",
        label="Rows",
    )
    n_rows
    return (n_rows,)


@app.cell
def _(n_rows, np):
    def make_clusters(n, n_dims=8, n_clusters=5, seed=0):
        rng = np.random.default_rng(seed)
        centers = rng.normal(scale=4.0, size=(n_clusters, n_dims))
        scales = rng.uniform(0.6, 1.6, size=(n_clusters, n_dims))
        labels = rng.integers(0, n_clusters, size=n)
        X = centers[labels] + rng.normal(size=(n, n_dims)) * scales[labels]
        # A couple of correlated dimensions make the cells less uniform.
        X[:, 1] += 0.6 * X[:, 0]
        X[:, 3] -= 0.4 * X[:, 2] ** 2 / 4
        return X.astype(np.float32), labels

    X, labels = make_clusters(n_rows.value)
    return X, labels


@app.cell(expand_output=True)
def _(PairPlot, X, labels, mo, np):
    pair_plot = PairPlot(
        X,
        columns=[f"feature_{i}" for i in range(X.shape[1])],
        color=np.char.add("cluster ", labels.astype(str)),
    )
    plot = mo.ui.anywidget(pair_plot)
    plot
    return pair_plot, plot


@app.cell
def _(labels, mo, np, pair_plot, plot):
    selection = plot.value["selection"]
    filters = plot.value["filters"]
    remaining = int(pair_plot.get_active_mask().sum())
    filter_note = (
        f"{len(filters)} filter(s) applied: "
        + ", ".join(step["action"] for step in filters)
        + f" → {remaining:,} of {len(labels):,} rows remain."
        if filters
        else ""
    )
    if selection:
        idx = pair_plot.get_indices()
        per_cluster = np.bincount(labels[idx], minlength=labels.max() + 1)
        x_name = pair_plot.columns[selection["x_index"]]
        y_name = pair_plot.columns[selection["y_index"]]
        lines = [
            f"**{len(idx):,}** of {remaining:,} rows selected with a {selection['type']} in `{x_name}` × `{y_name}`.",
            "",
            "| cluster | selected rows |",
            "| --- | ---: |",
        ]
        lines += [f"| cluster {i} | {count:,} |" for i, count in enumerate(per_cluster)]
        summary = mo.md("\n".join([filter_note, ""] + lines))
    else:
        summary = mo.md(filter_note or "_Drag a box in any scatter cell to select rows._")
    summary
    return


if __name__ == "__main__":
    app.run()
