# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy>=2.0.0",
#     "matplotlib",
#     "wigglystuff==0.2.36",
#     "polars==1.38.1",
# ]
# ///

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import numpy as np

    return (np,)


@app.cell
def _(mo):
    dimensions = mo.ui.slider(start=1, stop=20, step=1, value=5, label="Dimensions")
    n_points = mo.ui.slider(
        start=1000, stop=100000, step=1000, value=10000, label="Number of Points"
    )
    mo.hstack([dimensions, n_points])
    return dimensions, n_points


@app.cell
def _(dimensions, mo, n_points, np):
    @mo.cache
    def estimate_ball_fraction(dim, n_pts):
        points = np.random.uniform(-1, 1, size=(n_pts, dim))
        distances = np.sqrt(np.sum(points**2, axis=1))
        in_ball = np.mean(distances <= 1)
        return in_ball

    ball_fraction = estimate_ball_fraction(dimensions.value, n_points.value)
    return ball_fraction, estimate_ball_fraction, mo, n_points, np


@app.cell
def _(mo, n_points, np):
    @mo.cache
    def estimate_all_dimensions(n_pts):
        volumes = []
        for dim in range(1, 21):
            points = np.random.uniform(-1, 1, size=(n_pts, dim))
            distances = np.sqrt(np.sum(points**2, axis=1))
            in_ball = np.mean(distances <= 1)
            volumes.append(in_ball)
        return volumes

    all_volumes = estimate_all_dimensions(n_points.value)
    return all_volumes, estimate_all_dimensions, np


@app.cell
def _(all_volumes, ball_fraction, dimensions, mo, np):
    import matplotlib.pyplot as plt

    dim_range = np.arange(1, 21)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        dim_range,
        all_volumes,
        "o-",
        linewidth=2,
        markersize=6,
        label="Simulated Volume",
    )
    ax.scatter(
        [dimensions.value],
        [ball_fraction],
        color="red",
        s=150,
        zorder=5,
        label="Current Selection",
    )
    ax.axhline(y=0, color="black", linestyle="--", alpha=0.3)
    ax.set_xlabel("Number of Dimensions", fontsize=12)
    ax.set_ylabel("Volume (fraction of unit cube)", fontsize=12)
    ax.set_title("Unit Ball Volume Simulation", fontsize=14, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylim(1e-10, 1)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    plt.tight_layout()

    fig
    return ax, fig, plt


@app.cell
def _(dimensions, mo, n_points, np):
    @mo.cache
    def generate_points(dim, n_pts):
        points = np.random.uniform(-1, 1, size=(n_pts, dim))
        distances = np.sqrt(np.sum(points**2, axis=1))
        in_ball = distances <= 1
        return points, in_ball

    points, in_ball = generate_points(dimensions.value, n_points.value)

    import polars as pl

    data = {f"dim_{i + 1}": points[:, i] for i in range(dimensions.value)}
    data["inside_ball"] = in_ball.astype(str)

    df = pl.DataFrame(data)

    from wigglystuff import ParallelCoordinates

    parallel_chart = mo.ui.anywidget(
        ParallelCoordinates(df.head(500), color_by="inside_ball")
    )
    parallel_chart
    return df, in_ball, np, parallel_chart, points


if __name__ == "__main__":
    app.run()
