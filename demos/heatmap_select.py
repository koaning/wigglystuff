# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "wigglystuff==0.5.21",
# ]
# ///

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import marimo as mo
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import PowerNorm
    from wigglystuff import HeatmapSelect

    return HeatmapSelect, PowerNorm, matplotlib, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # HeatmapSelect

    A parameter space, in the spirit of Bret Victor's
    [*Up and Down the Ladder of Abstraction*](https://worrydream.com/LadderOfAbstraction/).

    Every cell is one cannon shot. Brightness is how far the ball travels before
    it hits the ground — and because there's air drag, the best angle isn't 45°.

    - **Hover the grid** to preview a single `(angle, speed)` shot. Hover the
      **left gutter** for a whole row (speed held, angle sweeps), or the
      **bottom gutter** for a whole column (angle held, speed sweeps).
    - **Click** to pin. The three pins are **independent and coexist** — pin a
      cell, then a row, then a column, and all three stay. Clicking a region
      only replaces that region's pin; hovering never disturbs any of them.
    - **Double-click** a region to drop just that pin.

    Each axis has its own colour, in the widget's bands *and* in the chart:
    <span style="color:#1f4fd8">**blue** for the y axis</span> (a row — speed
    held, angle sweeps) and <span style="color:#e07b00">**orange** for the x
    axis</span> (a column — angle held, speed sweeps). Hovering draws the same
    fan thin and transparent; pinning makes it solid. Making sense of a
    combination is the caller's job, not the widget's.

    Then drag the wind slider: the whole parameter space is recomputed and
    recolored, but your pins stay exactly where you put them.
    """)
    return


@app.cell
def _(np):
    # 91 columns x 100 rows, matching Victor's grid shape.
    ANGLES = np.linspace(0.0, 90.0, 91)  # degrees
    SPEEDS = np.linspace(5.0, 60.0, 100)  # m/s
    GRAVITY = 9.81
    DRAG = 0.002  # quadratic drag, 1/m
    DT = 0.01
    MAX_STEPS = 2000
    # Held fixed across every wind setting, so the chart frame never jumps.
    PLOT_LIMITS = (275.0, 150.0)
    # One color per axis, shared by the widget's bands and the chart's arcs so the
    # two read as the same thing. ROW comes off the y axis, COL off the x axis.
    ROW_COLOR = "#1f4fd8"
    COL_COLOR = "#e07b00"
    CELL_COLOR = "#111111"
    return (
        ANGLES,
        CELL_COLOR,
        COL_COLOR,
        DRAG,
        DT,
        GRAVITY,
        MAX_STEPS,
        PLOT_LIMITS,
        ROW_COLOR,
        SPEEDS,
    )


@app.cell
def _(DRAG, DT, GRAVITY, MAX_STEPS, np):
    def fire(angles_deg, speeds, wind=0.0, record=False):
        """Fire a cannon at every (angle, speed) pair at once.

        Args:
            angles_deg: 1D array of launch angles in degrees, the last axis.
            speeds: 1D array of launch speeds in m/s, the middle axis.
            wind: Horizontal wind in m/s; positive is a tailwind. Drag acts on
                velocity *relative to the air*, which is what lets wind bend the
                whole parameter space instead of just shifting it.
            record: Whether to also return the flight paths. Skipped for the full
                grid, where the arcs would be hundreds of megabytes.

        Returns:
            dict: ``distance`` shaped ``(len(speeds), len(angles))``, plus
                ``path_x``/``path_y`` shaped ``(MAX_STEPS, *that)`` when
                ``record`` is set (``None`` otherwise). Paths are ``nan`` after
                landing so plotted lines stop at the ground.
        """
        angle = np.deg2rad(np.asarray(angles_deg, dtype=float))[None, :]
        speed = np.asarray(speeds, dtype=float)[:, None]
        shape = np.broadcast(angle, speed).shape

        x = np.zeros(shape)
        y = np.zeros(shape)
        vx = np.broadcast_to(speed * np.cos(angle), shape).copy()
        vy = np.broadcast_to(speed * np.sin(angle), shape).copy()
        flying = np.ones(shape, dtype=bool)
        distance = np.zeros(shape)
        path_x = np.full((MAX_STEPS, *shape), np.nan) if record else None
        path_y = np.full((MAX_STEPS, *shape), np.nan) if record else None

        for step in range(MAX_STEPS):
            if not flying.any():
                break
            airborne = flying.copy()

            relative_vx = vx - wind
            v = np.hypot(relative_vx, vy)
            nvx = vx + DT * (-DRAG * v * relative_vx)
            nvy = vy + DT * (-GRAVITY - DRAG * v * vy)
            nx = x + DT * nvx
            ny = y + DT * nvy

            # Interpolate the ground crossing. Without this the range field has a
            # visible staircase from the fixed time step.
            landed = airborne & (ny < 0)
            if landed.any():
                frac = y[landed] / np.maximum(y[landed] - ny[landed], 1e-12)
                distance[landed] = x[landed] + frac * (nx[landed] - x[landed])
                flying &= ~landed

            x = np.where(flying, nx, x)
            y = np.where(flying, ny, y)
            vx = np.where(flying, nvx, vx)
            vy = np.where(flying, nvy, vy)

            if record:
                path_x[step] = np.where(airborne, nx, np.nan)
                path_y[step] = np.where(airborne, ny, np.nan)
                path_x[step][landed] = distance[landed]
                path_y[step][landed] = 0.0

        distance[flying] = x[flying]  # still airborne when the clock ran out
        return {"distance": distance, "path_x": path_x, "path_y": path_y}

    return (fire,)


@app.cell
def _(mo):
    wind = mo.ui.slider(
        -8.0, 8.0, step=0.5, value=0.0, label="wind (m/s)", show_value=True
    )
    wind
    return (wind,)


@app.cell
def _(ANGLES, COL_COLOR, HeatmapSelect, ROW_COLOR, SPEEDS, fire, mo):
    # Built ONCE, deliberately without referencing `wind`. The cell below mutates
    # this same widget via set_image() rather than constructing a new one — that
    # is what keeps a committed selection alive across a wind change.
    #
    # `grid` is exposed separately on purpose: marimo re-runs whichever cells
    # reference a UI element when you interact with it, so the wind cell reaches
    # the widget through `grid` instead of `heatmap`. Referencing `heatmap` there
    # would re-simulate the entire parameter space on every mouse move.
    grid = HeatmapSelect(
        fire(ANGLES, SPEEDS)["distance"],
        cmap="gray",
        # norm=PowerNorm(0.35),
        x_range=(ANGLES[0], ANGLES[-1]),
        y_range=(SPEEDS[0], SPEEDS[-1]),
        x_label="launch\nangle",
        y_label="speed",
        x_suffix="°",
        cell_width=4,
        cell_height=4,
        # Same hexes the chart below uses, so a blue band and a blue fan of arcs
        # are obviously the same selection.
        row_color=ROW_COLOR,
        col_color=COL_COLOR,
    )
    # Not displayed here — the chart cell renders it beside the trajectories.
    heatmap = mo.ui.anywidget(grid)
    return grid, heatmap


@app.cell
def _(ANGLES, SPEEDS, fire, grid, wind):
    # Recompute the parameter space for this wind and push only the bitmap.
    # set_image touches image_base64/n_rows/n_cols and nothing else, so
    # mode/row/col/pinned survive untouched.
    distance = fire(ANGLES, SPEEDS, wind=wind.value)["distance"]
    grid.set_image(distance)
    return (distance,)


@app.cell(hide_code=True)
def _(ANGLES, distance, heatmap, mo):
    # The three pins are independent, so this is three ifs, not a branch.
    lines = []
    if heatmap.pinned_cell is not None:
        pin_row, pin_col = heatmap.pinned_cell
        lines.append(
            f"- **cell** — {heatmap.x_at(pin_col):.0f}° at "
            f"{heatmap.y_at(pin_row):.0f} m/s travels "
            f"**{distance[pin_row, pin_col]:.0f} m**"
        )
    if heatmap.pinned_row is not None:
        best = distance[heatmap.pinned_row].argmax()
        lines.append(
            f"- **row** — at {heatmap.y_at(heatmap.pinned_row):.0f} m/s the "
            f"furthest is **{distance[heatmap.pinned_row, best]:.0f} m**, at "
            f"**{ANGLES[best]:.0f}°**"
        )
    if heatmap.pinned_col is not None:
        reach = distance[:, heatmap.pinned_col].max()
        lines.append(
            f"- **column** — at {heatmap.x_at(heatmap.pinned_col):.0f}° the "
            f"best any speed manages is **{reach:.0f} m**"
        )
    if not lines:
        lines = ["*Nothing pinned. Hover to preview, click to pin.*"]
    mo.md("\n".join(lines))
    return


@app.cell(hide_code=True)
def _(
    ANGLES,
    CELL_COLOR,
    COL_COLOR,
    PLOT_LIMITS,
    ROW_COLOR,
    SPEEDS,
    fire,
    heatmap,
    mo,
    plt,
    wind,
):
    # Abstracting over a parameter means drawing every run at once, the way
    # Victor overlays all the car trajectories for a swept road bend. Because the
    # three pins coexist, all three layers can be on screen together — deciding
    # what that combination should look like is exactly the caller's job.
    #
    # Sized to roughly match the widget's height so the two sit level in the
    # hstack at the bottom of this cell.
    fig, ax = plt.subplots(figsize=(5.4, 4.3))
    drew = False

    def fan(angles, speeds, **style):
        shots = fire(angles, speeds, wind=wind.value, record=True)
        xs = shots["path_x"].reshape(shots["path_x"].shape[0], -1)
        ys = shots["path_y"].reshape(shots["path_y"].shape[0], -1)
        ax.plot(xs, ys, **style)

    # Hover layers first, so a pin always draws over its own preview. Each keeps
    # its axis colour and just goes thin and transparent — coarser subsampling
    # too, since these redraw on every mouse move.
    if heatmap.hover_row is not None:
        fan(
            ANGLES[::6],
            [SPEEDS[heatmap.hover_row]],
            color=ROW_COLOR,
            linewidth=0.7,
            alpha=0.2,
        )
        drew = True

    if heatmap.hover_col is not None:
        fan(
            [ANGLES[heatmap.hover_col]],
            SPEEDS[::6],
            color=COL_COLOR,
            linewidth=0.7,
            alpha=0.25,
        )
        drew = True

    if heatmap.hover_cell is not None:
        hover_row, hover_col = heatmap.hover_cell
        fan(
            [ANGLES[hover_col]],
            [SPEEDS[hover_row]],
            color=CELL_COLOR,
            linewidth=1.0,
            alpha=0.35,
        )
        drew = True

    if heatmap.pinned_row is not None:
        # Speed held, every angle swept.
        fan(
            ANGLES[::3],
            [SPEEDS[heatmap.pinned_row]],
            color=ROW_COLOR,
            linewidth=0.8,
            alpha=0.45,
        )
        drew = True

    if heatmap.pinned_col is not None:
        # Angle held, every speed swept.
        fan(
            [ANGLES[heatmap.pinned_col]],
            SPEEDS[::3],
            color=COL_COLOR,
            linewidth=0.8,
            alpha=0.55,
        )
        drew = True

    if heatmap.pinned_cell is not None:
        # Slicing happens here in Python — the widget only reports indices.
        cell_row, cell_col = heatmap.pinned_cell
        fan([ANGLES[cell_col]], [SPEEDS[cell_row]], color=CELL_COLOR, linewidth=1.8)
        drew = True

    if not drew:
        ax.text(0.5, 0.5, "nothing selected", ha="center", va="center", color="#999999")
        ax.set_axis_off()
    else:
        # Fixed limits, so changing the wind swaps the curves without also
        # rescaling the frame underneath them.
        ax.set_xlim(0, PLOT_LIMITS[0])
        ax.set_ylim(0, PLOT_LIMITS[1])
        ax.axhline(0.0, color="#999999", linewidth=1.0)
        ax.set_xlabel("metres downrange")
        ax.set_ylabel("height (m)")
        ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()

    # The parameter space and the trajectories it stands for, side by side. The
    # widget is only *displayed* here, not created here, so re-running this cell
    # on hover reuses the same element rather than resetting it.
    mo.hstack([heatmap, fig], justify="start", align="center", gap=1.5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The coloring is just matplotlib

    `HeatmapSelect` takes a picture, one pixel per cell. Hand it a 2D array and
    it colormaps with matplotlib's own conventions — `cmap`, `norm`, `vmin`,
    `vmax` — defaulting to grayscale. Cells that are **masked or NaN** get the
    colormap's "bad" color, which is all you need for a Bret-Victor-style crash
    region. Below: shots that fail to clear 120 m are masked out in red.
    """)
    return


@app.cell
def _(ANGLES, HeatmapSelect, PowerNorm, SPEEDS, distance, matplotlib, mo, np):
    mo.ui.anywidget(
        HeatmapSelect(
            np.ma.masked_where(distance < 120.0, distance),
            cmap=matplotlib.colormaps["magma"].with_extremes(bad="#c81e1e"),
            norm=PowerNorm(0.35),
            x_range=(ANGLES[0], ANGLES[-1]),
            y_range=(SPEEDS[0], SPEEDS[-1]),
            x_label="launch\nangle",
            y_label="speed",
            x_suffix="°",
            cell_width=3,
            cell_height=3,
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## What the widget gives you

    The values behind the picture never cross the wire — the widget hands back
    indices plus data coordinates, and the slicing is yours:

    | Trait | Meaning |
    | --- | --- |
    | `pinned_cell` | `(row, col)` of the pinned cell, or `None` |
    | `pinned_row` | row index pinned from the left axis, or `None` |
    | `pinned_col` | column index pinned from the bottom axis, or `None` |
    | `hover_cell` / `hover_row` / `hover_col` | the same three shapes for the cursor; only one is ever set |

    All six are independent. `x_at(col)` and `y_at(row)` turn an index back into
    a data coordinate, and `clear()` drops everything.
    """)
    return


@app.cell
def _(heatmap):
    heatmap.selection
    return


if __name__ == "__main__":
    app.run()
