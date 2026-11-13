# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "wigglystuff==0.5.41",
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
        FloatingPanel,
        PairPlot,
        ScatterWidget,
        WidgetFlow,
        shape_display,
    )

    return (
        CircularSlider,
        FloatingPanel,
        PairPlot,
        ScatterWidget,
        WidgetFlow,
        mo,
        np,
        shape_display,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Draw a shape, project it, look at it

    Paint a shape in the canvas at the top. Every point becomes a row of a
    matrix $\mathbf{X}$ with two columns, its $x$ and $y$ position. Adding
    gaussian noise gives $\tilde{\mathbf{X}} = \mathbf{X} + \boldsymbol{\varepsilon}$,
    and multiplying by the $2 \times 4$ matrix $\mathbf{W}$ turns that into an
    $n \times 4$ matrix $\mathbf{Z} = \tilde{\mathbf{X}}\mathbf{W}$. A second
    round of noise, now in all four columns, gives
    $\tilde{\mathbf{Z}} = \mathbf{Z} + \boldsymbol{\varepsilon}_4$, and a
    rotation $\mathbf{R}$ by an angle $\theta$ in four dimensions turns that
    into $\mathbf{Y} = \tilde{\mathbf{Z}}\mathbf{R}$. Principal component
    analysis of $\mathbf{Y}$ gives the scores $\mathbf{P}$: the same points
    in new axes, sorted by how much the points spread along them. The three
    pair plots at the bottom show how the four columns are distributed in
    $\mathbf{Z}$, before the second noise and the rotation, in $\mathbf{Y}$,
    after both, and in $\mathbf{P}$.

    The default $\mathbf{W}$ keeps $x$ and $y$ and adds $x + y$ and $x - y$.
    Noise that goes in before $\mathbf{W}$ keeps the new columns exact mixes
    of the first two, so the points stay on a flat plane in four dimensions;
    noise after $\mathbf{W}$ shakes them off it. Drag the numbers in
    $\mathbf{W}$ to mix the columns differently, the sliders to set the
    standard deviation of either noise (in canvas pixels), and the dial to
    rotate.

    In four dimensions a rotation turns two planes at once. The button picks
    a new random pair of planes, and the dial turns both of them by
    $\theta$: at $0°$ nothing is rotated, and a full turn brings every point
    back to where it started. A rotation keeps every distance between points,
    so the shape is still in there, just seen from a new angle.

    That is also why the PCA plot doesn't move when you turn the dial: PCA
    finds the directions of largest spread, and a rotation turns those
    directions along with the data, so it lands on the same principal
    components every time: PCA undoes the rotation.

    It can't undo the noise, though. With no noise after $\mathbf{W}$ the
    points lie on a plane, so the first two principal components hold all
    the spread and the last two are flat. Turn up the second noise and watch
    them fill in.
    """)
    return


@app.cell
def _(np):
    # A noisy ring to start from, in the canvas's pixel coordinates.
    _rng = np.random.default_rng(0)
    _angle = _rng.uniform(0, 2 * np.pi, 150)
    _radius = 100 + _rng.normal(0, 8, 150)
    starting_points = [
        {"x": 250 + r * np.cos(a), "y": 150 + r * np.sin(a), "color": "#1f77b4", "label": "a", "batch": 0}
        for a, r in zip(_angle, _radius)
    ]
    return (starting_points,)


@app.cell
def _(np):
    def random_basis(seed):
        """A uniformly random orthonormal basis of 4D space.

        QR of a gaussian matrix gives an orthogonal Q; matching its signs to
        R's diagonal makes it uniformly random.
        """
        q, r = np.linalg.qr(np.random.default_rng(seed).normal(size=(4, 4)))
        return q * np.sign(np.diag(r))

    def rotation_at(basis, theta):
        """Turn by ``theta`` radians in two planes at once: the one spanned by
        the basis' first two columns and the one spanned by its last two."""
        c, s = np.cos(theta), np.sin(theta)
        turn = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, c, -s], [0, 0, s, c]])
        return basis @ turn @ basis.T

    return random_basis, rotation_at


@app.cell(expand_output=True)
def _(
    CircularSlider,
    FloatingPanel,
    PairPlot,
    ScatterWidget,
    WidgetFlow,
    mo,
    np,
    shape_display,
    starting_points,
):
    # Everything on screen is made here, once. marimo never reruns the cell
    # that defines a UI element when that element changes, so the flow is
    # drawn a single time and its widgets stay put. The cells below compute
    # the arrays and push them into the pair plots with `set_data`.
    drawing = mo.ui.anywidget(
        ScatterWidget(data=starting_points, n_classes=3, width=500, height=300)
    )
    noise = mo.ui.slider(0, 50, step=1, value=10, show_value=True)
    noise_4d = mo.ui.slider(0, 50, step=1, value=0, show_value=True)
    weights = mo.ui.matrix(
        [[1, 0, 1, 1], [0, 1, 1, -1]],
        min_value=-5,
        max_value=5,
        step=0.1,
        row_labels=["x", "y"],
        column_labels=["z1", "z2", "z3", "z4"],
    )
    new_planes = mo.ui.button(
        label="new random planes", value=0, on_click=lambda count: count + 1
    )
    angle = mo.ui.anywidget(
        CircularSlider(value=0, start=0, stop=360, step=1, size=120, label="θ (degrees)")
    )
    # A placeholder row each until the cells below send the real data.
    plot_before = PairPlot(
        np.zeros((1, 4)),
        columns=["z1", "z2", "z3", "z4"],
        cell_size=80,
        show_filters=False,
        show_layout_toggle=False,
        show_mode_toggle=False,
    )
    plot_after = PairPlot(
        np.zeros((1, 4)),
        columns=["y1", "y2", "y3", "y4"],
        cell_size=80,
        show_filters=False,
        show_layout_toggle=False,
        show_mode_toggle=False,
    )
    plot_pca = PairPlot(
        np.zeros((1, 4)),
        columns=["pc1", "pc2", "pc3", "pc4"],
        cell_size=80,
        show_filters=False,
        show_layout_toggle=False,
        show_mode_toggle=False,
    )

    # The arrays are only ever "n × 2" or "n × 4", so the flow shows their
    # shape with stand-ins rather than depending on (and redrawing for) them.
    X_shape = shape_display(np.empty((0, 2)), labels=("n", None), name=r"$\mathbf{X}$")
    X_noisy_shape = shape_display(
        np.empty((0, 2)), labels=("n", None), name=r"$\tilde{\mathbf{X}}$"
    )
    Z_shape = shape_display(np.empty((0, 4)), labels=("n", None), name=r"$\mathbf{Z}$")
    Z_noisy_shape = shape_display(
        np.empty((0, 4)), labels=("n", None), name=r"$\tilde{\mathbf{Z}}$"
    )
    Y_shape = shape_display(np.empty((0, 4)), labels=("n", None), name=r"$\mathbf{Y}$")

    # The pair plots share one node: a small flow of their own, with Z and Y
    # side by side and the PCA arrow running down out of Y.
    before_panel = mo.vstack(
        [plot_before, mo.md("before the noise and rotation, $\\mathbf{Z}$")], align="center"
    )
    after_panel = mo.vstack(
        [plot_after, mo.md("after the noise and rotation, $\\mathbf{Y}$")], align="center"
    )
    pca_panel = mo.vstack(
        [plot_pca, mo.md("principal components, $\\mathbf{P}$")], align="center"
    )
    plots = WidgetFlow(
        [before_panel, after_panel, pca_panel],
        edges=[(after_panel, pca_panel, "PCA")],
        # one shared grid packed to the right, so PCA lands in Y's column
        align="right",
    )

    flow = WidgetFlow(
        [drawing, X_shape, noise, X_noisy_shape, weights, Z_shape, noise_4d, Z_noisy_shape, new_planes, angle, Y_shape, plots],
        edges=[
            (drawing, X_shape),
            (X_shape, X_noisy_shape),
            (noise, X_noisy_shape),
            (X_noisy_shape, Z_shape),
            (weights, Z_shape),
            (Z_shape, Z_noisy_shape),
            (noise_4d, Z_noisy_shape),
            (Z_noisy_shape, Y_shape),
            # the button picks the planes, the dial how far to turn in them
            (new_planes, angle, {"exit": "left", "enter": "right"}),
            (angle, Y_shape),
            # Z leaves on the left, around the steps below it, to land on its
            # plot on the left half; Y lands on the after plot on the right half.
            (Z_shape, plots, {"exit": "left", "enter": ("top", 0.25)}),
            (Y_shape, plots, {"enter": ("top", 0.75)}),
        ],
        labels=[
            (drawing, "drawing"),
            (X_shape, "X"),
            (noise, "noise"),
            (X_noisy_shape, "X_noisy"),
            (weights, "weights"),
            (Z_shape, "Z"),
            (noise_4d, "noise_4d"),
            (Z_noisy_shape, "Z_noisy"),
            (new_planes, "planes"),
            (angle, "angle"),
            (Y_shape, "Y"),
        ],
        beside=[
            (noise, X_noisy_shape),
            (weights, Z_shape),
            (noise_4d, Z_noisy_shape),
            (angle, Y_shape),
            (new_planes, Y_shape),
        ],
        align="left",
    )

    # The same controls again in a panel that floats over the page, so they
    # stay in reach while you scroll down to the plots. They are the same
    # objects as in the flow, so moving one moves the other.
    def _row(caption, control):
        return mo.hstack([mo.md(f"`{caption}`"), control], justify="start", align="center")

    panel = FloatingPanel(
        mo.vstack(
            [
                _row("noise", noise),
                _row("weights", weights),
                _row("noise_4d", noise_4d),
                mo.hstack([angle, new_planes], justify="start", align="center"),
            ],
            gap=0.75,
        ),
        title="controls",
        corner="top-right",
    )

    mo.vstack([flow, panel])
    return (
        angle,
        drawing,
        new_planes,
        noise,
        noise_4d,
        plot_after,
        plot_before,
        plot_pca,
        weights,
    )


@app.cell
def _(drawing, np, shape_display):
    _points = drawing.value["data"]
    X = shape_display(
        np.array([[p["x"], p["y"]] for p in _points]).reshape(-1, 2),
        labels=("n", None),
        name=r"$\mathbf{X}$",
    )
    labels = np.array([p["label"] for p in _points])
    label_colors = {p["label"]: p["color"] for p in _points}
    return X, label_colors, labels


@app.cell
def _(X, noise, np):
    # A fixed seed, so the slider scales the same noise instead of redrawing it.
    _epsilon = np.random.default_rng(0).normal(size=X.shape)
    X_noisy = (X + noise.value * _epsilon).set_name(r"$\tilde{\mathbf{X}}$")
    return (X_noisy,)


@app.cell
def _(X_noisy, np, weights):
    Z = (X_noisy @ np.array(weights.value)).set_name(r"$\mathbf{Z}$")
    return (Z,)


@app.cell
def _(Z, noise_4d, np):
    # Its own fixed seed, independent of the first noise.
    _epsilon = np.random.default_rng(1).normal(size=Z.shape)
    Z_noisy = (Z + noise_4d.value * _epsilon).set_name(r"$\tilde{\mathbf{Z}}$")
    return (Z_noisy,)


@app.cell
def _(new_planes, random_basis):
    # Each click is a new seed, so a new pair of planes to turn in.
    basis = random_basis(new_planes.value)
    return (basis,)


@app.cell
def _(Z_noisy, angle, basis, np, rotation_at):
    R = rotation_at(basis, np.radians(angle.value["value"]))
    Y = (Z_noisy @ R).set_name(r"$\mathbf{Y}$")
    return (Y,)


@app.cell
def _(Y, mo, np, shape_display):
    mo.stop(len(Y) < 4)
    # PCA by hand: centre the columns, and the SVD's U·S are the scores, the
    # points in principal-component axes, largest spread first.
    _centred = Y.value - Y.value.mean(axis=0)
    _u, _s, _ = np.linalg.svd(_centred, full_matrices=False)
    # The SVD picks each component's sign arbitrarily. Make the largest score
    # of each one positive so the plot doesn't flip as the inputs change.
    _signs = np.sign(_u[np.abs(_u).argmax(axis=0), np.arange(4)])
    explained = _s**2 / np.sum(_s**2)
    _scores = _u * _s * _signs
    # A component with no spread at all (the plane's missing directions, with
    # no noise after W) holds only rounding error; show it as the flat zero
    # it really is rather than blow that error up to fill the axes.
    _scores[:, explained < 1e-9] = 0
    P = shape_display(_scores, labels=("n", None), name=r"$\mathbf{P}$")
    return P, explained


@app.cell
def _(P, explained, label_colors, labels, plot_pca):
    plot_pca.set_data(
        P.value,
        # each component with the share of the total spread it holds
        columns=[f"pc{i + 1} · {share:.0%}" for i, share in enumerate(explained)],
        color=labels if len(label_colors) > 1 else None,
        color_map=label_colors,
    )
    return


@app.cell
def _(Z, label_colors, labels, plot_before):
    # Update the plots in place: the points move, nothing gets re-created.
    # A legend only helps when there is more than one class to tell apart.
    if len(Z) > 0:
        plot_before.set_data(
            Z.value,
            columns=["z1", "z2", "z3", "z4"],
            color=labels if len(label_colors) > 1 else None,
            color_map=label_colors,
        )
    return


@app.cell
def _(Y, label_colors, labels, plot_after):
    if len(Y) > 0:
        plot_after.set_data(
            Y.value,
            columns=["y1", "y2", "y3", "y4"],
            color=labels if len(label_colors) > 1 else None,
            color_map=label_colors,
        )
    return


if __name__ == "__main__":
    app.run()
