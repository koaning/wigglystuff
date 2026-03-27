# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy==2.4.3",
#     "matplotlib==3.10.8",
#     "wigglystuff==0.2.37",
#     "polars==1.38.1",
# ]
# ///

import marimo

__generated_with = "0.20.4"
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
        start=1000, stop=1000000, step=1000, value=100000, label="Number of Points"
    )
    mo.hstack([dimensions, n_points])
    return dimensions, n_points


@app.cell
def _(fig):
    fig
    return


@app.cell
def _(dimensions, mo, n_points):
    mo.hstack([dimensions, n_points])
    return


@app.cell
def _(in_ball, plt, points):
    plt.figure(figsize=(7, 7))
    plt.scatter(points[:, 0], points[:, 1], c=in_ball, s=3)
    return


@app.cell
def _(mo):
    opacity = mo.ui.slider(0, 1, 0.01, label="opacity", value=1)
    return (opacity,)


@app.cell
def _(dimensions, mo, n_points, opacity):
    mo.hstack([dimensions, n_points, opacity])
    return


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(df):
    df
    return


@app.cell
def _(df, dimensions, opacity, pl):
    from wigglystuff import ThreeWidget

    _points = (
        df.with_columns(
            dim_2=pl.col("dim_2") if dimensions.value >= 2 else pl.lit(0),
            dim_3=pl.col("dim_3") if dimensions.value >= 3 else pl.lit(0),
        )
        .with_columns(pl.col("inside_ball") == "true")
        .rename(dict(dim_1="x", dim_2="y", dim_3="z"))
        .with_columns(
            opacity=opacity.value + (1 - opacity.value) * pl.col("inside_ball").cast(pl.Int8),
            color=pl.when(pl.col("inside_ball")).then(pl.lit("yellow")).otherwise(pl.lit("purple")),
            size=pl.lit(0.05),
        )
        .to_dicts()
    )

    widget = ThreeWidget(data=_points, dark_mode=True, xlim=(-1, 1), ylim=(-1, 1), zlim=(-1, 1))
    return ThreeWidget, widget


@app.cell
def _(dimensions, mo, n_points, np):
    @mo.cache
    def estimate_ball_fraction(dim, n_pts):
        points = np.random.uniform(-1, 1, size=(n_pts, dim))
        distances = np.sqrt(np.sum(points**2, axis=1))
        in_ball = np.mean(distances <= 1)
        return in_ball


    ball_fraction = estimate_ball_fraction(dimensions.value, n_points.value)
    return (ball_fraction,)


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
    return (all_volumes,)


@app.cell
def _(all_volumes, ball_fraction, dimensions, np):
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
    ax.set_ylim(1e-10, 1)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    plt.tight_layout()
    return fig, plt


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
    data["inside_ball"] = in_ball

    df = pl.DataFrame(data).with_columns(inside_ball=pl.col("inside_ball").cast(pl.String()))
    return df, in_ball, pl, points


@app.cell
def _(df, mo):
    from wigglystuff import ParallelCoordinates

    parallel_chart = mo.ui.anywidget(
        ParallelCoordinates(
            df, color_by="inside_ball", height=500, color_map={"true": "yellow", "false": "purple"}
        )
    )
    return ParallelCoordinates, parallel_chart


@app.cell
def _(dimensions, mo, n_points, opacity):
    mo.hstack([dimensions, n_points, opacity])
    return


@app.cell
def _(parallel_chart):
    parallel_chart
    return


@app.cell
def _(another_three_widget):
    another_three_widget
    return


@app.cell
def _(parallel_chart, pl):
    pl.DataFrame(parallel_chart.filtered_data)
    return


@app.cell
def _(ThreeWidget, opacity, parallel_chart, pl):
    _df = pl.DataFrame(parallel_chart.filtered_data)

    _points = (
        _df.rename(dict(dim_1="x", dim_2="y", dim_3="z"))
        .with_columns(pl.col("inside_ball") == "true")
        .with_columns(
            opacity=opacity.value + (1 - opacity.value) * pl.col("inside_ball").cast(pl.Int8),
            color=pl.when(pl.col("inside_ball")).then(pl.lit("yellow")).otherwise(pl.lit("purple")),
            size=pl.lit(0.05),
        )
        .to_dicts()
    )

    another_three_widget = ThreeWidget(
        data=_points, dark_mode=True, xlim=(-1, 1), ylim=(-1, 1), zlim=(-1, 1)
    )
    return (another_three_widget,)


@app.cell
def _(dimensions, n_points, np, pl):
    samples = np.random.normal(0, 1, (n_points.value, dimensions.value))
    normalized = samples / np.linalg.norm(samples, axis=1, keepdims=True)
    pltr = pl.DataFrame({f"surf_{i+1}": normalized[:, i] for i in range(dimensions.value)})
    return (pltr,)


@app.cell
def _(dimensions, mo, n_points, opacity):
    mo.hstack([dimensions, n_points, opacity])
    return


@app.cell
def _(ParallelCoordinates, mo, pltr):
    parallel_surface = mo.ui.anywidget(
        ParallelCoordinates(
            pltr,
            color_by="inside_ball",
            height=500,
            color_map={"true": "yellow", "false": "purple"},
        )
    )
    parallel_surface
    return (parallel_surface,)


@app.cell
def _(surface_three):
    surface_three
    return


@app.cell
def _(ThreeWidget, parallel_surface, pl):
    _df = pl.DataFrame(parallel_surface.selected_data)

    _points = (
        _df.rename(dict(surf_1="x", surf_2="y", surf_3="z"))
        .with_columns(size=pl.lit(0.05), opacity=pl.lit(0.1))
        .to_dicts()
    )

    surface_three = ThreeWidget(data=_points, dark_mode=True)
    return (surface_three,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
