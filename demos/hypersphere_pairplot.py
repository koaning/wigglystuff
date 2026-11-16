# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "wigglystuff==0.6.0",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path

    # Prefer the local checkout so the demo works before the next release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    import marimo as mo
    import numpy as np
    from wigglystuff import (
        CircularSlider,
        PairPlot,
        ThreeWidget,
        WidgetFlow,
        shape_display,
    )

    return (
        CircularSlider,
        PairPlot,
        ThreeWidget,
        WidgetFlow,
        mo,
        np,
        shape_display,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A pair plot of a sphere in four dimensions

    You can't look at a sphere in four dimensions, but you can look at its
    shadows. A pair plot does exactly that: every cell drops all coordinates
    but two and shows what is left, so every cell is the sphere's shadow on
    one plane.

    The points are made in two steps. First draw an $n \times d$ matrix
    $\mathbf{G}$ of standard gaussian numbers. A gaussian looks the same in
    every direction, so each row points somewhere uniformly at random. Then
    divide each row by its length $\lVert\mathbf{G}\rVert$: every row of
    $\mathbf{X}$ now has length one, which is to say it lies on the unit
    sphere, spread evenly over it. The thickness slider shakes the length a
    little so the sphere gets a fuzzy shell.

    Every shadow is a disk, but how the points fill it depends on $d$. In
    three dimensions they pile up at the rim, in four they fill the disk
    evenly, and in five they crowd the middle. The histograms on the diagonal
    tell the same story: one coordinate of a point on the sphere has density
    proportional to $(1 - x^2)^{(d-3)/2}$, flat for $d = 3$, a semicircle for
    $d = 4$, a parabola for $d = 5$. The more dimensions, the more of the
    sphere sits near the "equator" of any one axis.
    """)
    return


@app.cell(expand_output=True)
def _(
    CircularSlider,
    PairPlot,
    ThreeWidget,
    WidgetFlow,
    mo,
    np,
    shape_display,
):
    # Everything on screen is made here, once. marimo never reruns the cell
    # that defines a UI element when that element changes, so the flow is
    # drawn a single time and its widgets keep their state. The cells below
    # compute the arrays and push them into the pair plot with `set_data`.
    dims = mo.ui.radio(
        {"3D": 3, "4D": 4, "5D": 5}, value="4D", inline=True, label="dimensions"
    )
    n_points = mo.ui.slider(
        100, 20_000, step=100, value=3_000, show_value=True, full_width=True,
        label="points per sphere",
    )
    inner = mo.ui.switch(value=False, label="inner sphere, radius √½")
    thickness = mo.ui.slider(
        0, 0.3, step=0.01, value=0.0, show_value=True, full_width=True,
        label="thickness",
    )
    new_planes = mo.ui.button(
        label="new random planes", value=0, on_click=lambda count: count + 1
    )
    angle = mo.ui.anywidget(
        CircularSlider(value=0, start=0, stop=360, step=1, size=90, label="θ (degrees)")
    )
    # Controls that feed the same step share one node. A fixed width, so a
    # slider's number growing (100 -> 20,000) can't resize the node and nudge
    # the arrows.
    data_controls = mo.vstack([dims, n_points, inner], gap=0.75).style(width="260px")
    shell_controls = mo.vstack([thickness]).style(width="200px")
    rotation_controls = mo.vstack([angle, new_planes], align="center", gap=0.5)

    # A placeholder row until the cells below send the real data.
    plot = PairPlot(
        np.zeros((1, 4)),
        columns=["y1", "y2", "y3", "y4"],
        cell_size=114,
        show_filters=False,
        show_layout_toggle=False,
        show_mode_toggle=False,
    )
    # Fixed limits, so the camera and the grid never move when the data does.
    three = ThreeWidget(
        data=[],
        width=420,
        height=420,
        xlim=(-1.2, 1.2),
        ylim=(-1.2, 1.2),
        zlim=(-1.2, 1.2),
        show_grid=True,
        axis_labels=["y1", "y2", "y3"],
    )

    # Mirror the pair plot's selection in the 3D view: selected rows keep
    # their sphere's colour (stored on each point as "base"), the rest fade
    # to grey, like they do in the pair plot itself. An observer on the
    # widget, rather than a marimo cell, so a selection only recolours the
    # 3D points and nothing else reruns.
    def paint_selection(change=None):
        if len(three.data) != len(plot.get_mask()):
            return  # the two are mid-update after a new Y; the next one lands
        if not plot.selection:
            look = [{"color": p["base"], "opacity": 1.0} for p in three.data]
        else:
            look = [
                {"color": p["base"], "opacity": 1.0}
                if picked
                else {"color": "#c4c3bc", "opacity": 0.25}
                for p, picked in zip(three.data, plot.get_mask().tolist())
            ]
        three.update_points(look)

    plot.observe(paint_selection, names="selection")

    # The flow can't depend on `dims` (that would rebuild it, and reset the
    # sliders, on every toggle), so it shows the shapes symbolically. The live
    # sizes are in the row under the flow.
    G_shape = shape_display(np.empty((0, 4)), labels=("n", "d"), name=r"$\mathbf{G}$")
    r_shape = shape_display(
        np.empty((0, 1)), labels=("n", None), name=r"$\lVert\mathbf{G}\rVert$"
    )
    X_shape = shape_display(np.empty((0, 4)), labels=("n", "d"), name=r"$\mathbf{X}$")
    Y_shape = shape_display(np.empty((0, 4)), labels=("n", "d"), name=r"$\mathbf{Y}$")

    flow = WidgetFlow(
        [data_controls, G_shape, r_shape, shell_controls, X_shape, rotation_controls, Y_shape, plot, three],
        edges=[
            (data_controls, G_shape, "n, d"),
            (G_shape, r_shape, {"label": "row lengths", "exit": "left", "enter": "right"}),
            (G_shape, X_shape),
            (r_shape, X_shape, "divide"),
            (shell_controls, X_shape),
            (X_shape, Y_shape),
            (rotation_controls, Y_shape, "rotate"),
            (Y_shape, plot),
            (Y_shape, three, "first 3 columns"),
        ],
        labels=[
            (data_controls, "sample"),
            (G_shape, "G"),
            (r_shape, "lengths"),
            (shell_controls, "shell"),
            (X_shape, "X"),
            (rotation_controls, "rotation"),
            (Y_shape, "Y"),
            (plot, "pair plot of Y"),
            (three, "y1, y2, y3 in 3D"),
        ],
        notes=[
            (G_shape, "gaussian: the same in every direction"),
            (X_shape, "every row has length 1 (√½ on the inner sphere)"),
        ],
        beside=[
            (r_shape, G_shape, "before"),
            (shell_controls, X_shape, "before"),
            (rotation_controls, Y_shape),
            (three, plot),
        ],
        align="left",
        collapsible=[plot, three],
        # the tab on each dashed frame folds that stretch into one pill
        groups=[
            ("put the points on a sphere", [G_shape, r_shape, shell_controls, X_shape]),
            ("rotate", [rotation_controls, Y_shape]),
        ],
    )
    flow
    return angle, dims, inner, n_points, new_planes, plot, thickness, three


@app.cell
def _():
    SPHERE_COLORS = {"outer": "#1f77b4", "inner": "#ff7f0e"}
    return (SPHERE_COLORS,)


@app.cell
def _(dims, inner, n_points, np, shape_display):
    # Fixed seeds, so moving the slider adds points instead of reshuffling.
    # The inner sphere gets its own draw: as many rows, in directions of its own.
    _size = (n_points.value, dims.value)
    _rows = [np.random.default_rng(0).normal(size=_size)]
    if inner.value:
        _rows.append(np.random.default_rng(2).normal(size=_size))
    G = shape_display(np.vstack(_rows), name=r"$\mathbf{G}$")
    # Which sphere each row lands on, and its radius: x1² + ... + xd² = 1 on
    # the outer sphere and 1/2 on the inner one.
    sphere = np.repeat(["outer", "inner"][: len(_rows)], n_points.value)
    radius = np.where(sphere == "inner", 0.5**0.5, 1.0)[:, None]
    return G, radius, sphere


@app.cell
def _(G, np):
    r = np.linalg.norm(G, axis=1, keepdims=True).set_name(r"$\lVert\mathbf{G}\rVert$")
    return (r,)


@app.cell
def _(G, np, r, radius, thickness):
    # Its own fixed seed: the slider scales the same jitter instead of redrawing it.
    _eps = np.random.default_rng(1).normal(size=r.shape)
    X = (G / r * radius * (1 + thickness.value * _eps)).set_name(r"$\mathbf{X}$")
    return (X,)


@app.cell
def _(np):
    def random_basis(d, seed):
        """A uniformly random orthonormal basis of d-dimensional space.

        QR of a gaussian matrix gives an orthogonal Q; matching its signs to
        R's diagonal makes it uniformly random.
        """
        q, r = np.linalg.qr(np.random.default_rng(seed).normal(size=(d, d)))
        return q * np.sign(np.diag(r))

    def rotation_at(basis, theta):
        """Turn by ``theta`` radians in the planes spanned by the basis'
        columns 1-2, 3-4, ...: one plane in 3D (the third axis stays put),
        two in 4D, two in 5D (and the fifth axis stays put)."""
        c, s = np.cos(theta), np.sin(theta)
        turn = np.eye(len(basis))
        for k in range(0, len(basis) - 1, 2):
            turn[k : k + 2, k : k + 2] = [[c, -s], [s, c]]
        return basis @ turn @ basis.T

    return random_basis, rotation_at


@app.cell
def _(dims, new_planes, random_basis):
    # Each click is a new seed, so a new set of planes to turn in.
    basis = random_basis(dims.value, new_planes.value)
    return (basis,)


@app.cell
def _(X, angle, basis, np, rotation_at):
    R = rotation_at(basis, np.radians(angle.value["value"]))
    Y = (X @ R).set_name(r"$\mathbf{Y}$")
    return (Y,)


@app.cell
def _(SPHERE_COLORS, Y, plot, sphere):
    # Update the plot in place: the points move, nothing gets re-created.
    # The cells shrink as d grows so the plot keeps one size: d cells plus
    # the 6px gaps between them come to 474px for d = 3, 4 and 5.
    # hold_sync sends the new size and the new data in one message.
    with plot.hold_sync():
        plot.cell_size = 480 // Y.shape[1] - 6
        plot.set_data(
            Y.value,
            columns=[f"y{i + 1}" for i in range(Y.shape[1])],
            color=sphere,
            color_map=SPHERE_COLORS,
        )
    return


@app.cell
def _(SPHERE_COLORS, Y, sphere, three):
    three.data = [
        {"x": x, "y": y, "z": z, "size": 0.03, "color": c, "base": c, "opacity": 1.0}
        for (x, y, z), c in zip(
            Y.value[:, :3].tolist(), [SPHERE_COLORS[s] for s in sphere]
        )
    ]
    return


@app.cell
def _(G, X, Y, mo, r):
    mo.vstack(
        [
            mo.md("The same arrays, at their live sizes:"),
            mo.hstack([G, r, X, Y], justify="start", gap=3),
        ]
    )
    return


@app.cell(hide_code=True)
def _(dims, mo):
    _look = {
        3: r"""
        **3D.** One coordinate is *uniform* on $[-1, 1]$: the exponent
        $(d-3)/2$ is zero, so the diagonal histograms are flat. This is
        Archimedes' hat-box theorem: slice a sphere into bands of equal
        height and each has the same area. The shadows pile up at the rim,
        where the sphere's surface is seen edge-on.
        """,
        4: r"""
        **4D.** One coordinate has density $\propto (1 - x^2)^{1/2}$, a
        semicircle. Any two coordinates are spread *uniformly* over the disk:
        every off-diagonal cell is an evenly filled circle, with no rim and no
        crowd in the middle.
        """,
        5: r"""
        **5D.** One coordinate has density $\propto 1 - x^2$, a parabola. The
        shadows crowd the centre: with more dimensions to share the unit
        length between, any two coordinates tend to be small together.
        """,
    }
    mo.md(_look[dims.value])
    return


if __name__ == "__main__":
    app.run()
