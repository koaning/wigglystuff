# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.19",
#     "matplotlib==3.10.8",
#     "numpy==2.4.1",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from pathlib import Path
    import sys

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import CubeWidget

    return (CubeWidget,)


@app.cell
def _(CubeWidget, mo):
    cube_view = mo.ui.anywidget(CubeWidget(
        x_axis={"name": "Angle", "values": [i for i in range(0, 90, 5)]},
        y_axis={"name": "Force", "values": [i * 5 for i in range(21)]},
        z_axis={"name": "Time", "values": [i * 0.2 for i in range(91)]},
    ))
    return (cube_view,)


@app.cell
def _(cube_view, mo):
    cube = cube_view.widget
    mo.md(f"""
    ## Widget State

    - **Plane**: {cube.plane}
    - **Line**: {cube.line}
    - **Point**: {cube.point}

    ---

    **Locked order**: {cube.locked_order}

    **Axis values**: {cube.axis_values}
    """)
    return


@app.cell
def _():
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    return np, pd, plt


@app.cell
def _(np, pd):
    _axis_columns = {"x": "angle", "y": "force", "z": "time"}

    def build_trajectory_frame(state):
        locked = set(state["locked_order"])
        samples = {}
        for axis, column in _axis_columns.items():
            values = list(state[f"{axis}_axis"]["values"])
            if axis in locked:
                values.append(state["axis_values"][axis])
            samples[column] = sorted(set(values))

        frame = pd.MultiIndex.from_product(
            [samples["angle"], samples["force"], samples["time"]],
            names=["angle", "force", "time"],
        ).to_frame(index=False)

        angle_radians = np.radians(frame["angle"])
        frame["distance"] = (
            frame["force"] * np.cos(angle_radians) * frame["time"]
        )
        frame["height"] = (
            frame["force"] * np.sin(angle_radians) * frame["time"]
            - 0.5 * 9.8 * frame["time"] ** 2
        ).clip(lower=0)
        return frame

    def filter_frame(frame, axes, axis_values):
        for axis in axes:
            column = _axis_columns[axis]
            frame = frame[frame[column] == axis_values[axis]]
        return frame

    return build_trajectory_frame, filter_frame


@app.cell
def _(build_trajectory_frame, cube_view, filter_frame, plt):
    state = cube_view.value
    axis_values = state["axis_values"]
    locked_order = state["locked_order"]
    frame = build_trajectory_frame(state)

    def draw_slice(ax, sliced, locked_axes, color, alpha, linewidth, size):
        if "z" in locked_axes:
            ax.scatter(
                sliced["distance"], sliced["height"],
                color=color, alpha=alpha, s=size,
            )
            return
        for _, trajectory in sliced.groupby(["angle", "force"]):
            ax.plot(
                trajectory["distance"], trajectory["height"],
                color=color, alpha=alpha, linewidth=linewidth,
            )

    fig, ax = plt.subplots(figsize=(8, 6))

    axis_colors = {"x": "#e74c3c", "y": "#27ae60", "z": "#3498db"}
    layer_axes = [locked_order[:1], locked_order[:2]][
        :min(2, max(1, len(locked_order)))
    ]

    for index, axes in enumerate(layer_axes):
        color = axis_colors[axes[-1]] if axes else "#95a5a6"
        alpha, linewidth, size = [(0.25, 1, 18), (0.8, 2, 32)][index]
        sliced = filter_frame(frame, axes, axis_values)
        draw_slice(
            ax, sliced, axes, color, alpha, linewidth, size,
        )

    if len(locked_order) == 3:
        point = filter_frame(frame, locked_order, axis_values)
        ax.scatter(
            point["distance"], point["height"],
            color=axis_colors[locked_order[2]],
            edgecolor="black", linewidth=2,
            s=180, zorder=10,
        )

    level = ["Volume", "Plane", "Line", "Point"][len(locked_order)]
    selections = [
        f'{state[f"{axis}_axis"]["name"]}={axis_values[axis]:g}'
        for axis in locked_order
    ]
    detail = ", ".join(selections) if selections else "all free"
    ax.set_title(f"{level}: {detail}")
    ax.axhline(y=0, color="green", linewidth=2, alpha=0.5)
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Height (m)")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 300)

    plt.tight_layout()
    trajectory_chart = fig
    return (trajectory_chart,)


@app.cell
def _(cube_view, mo, trajectory_chart):
    mo.hstack([cube_view, trajectory_chart], justify="start", gap=1)
    return


if __name__ == "__main__":
    app.run()
