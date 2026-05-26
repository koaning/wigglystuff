# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "wigglystuff==0.5.4",
# ]
# ///

import marimo

__generated_with = "0.23.7"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    from wigglystuff import CurveEditor, Slider2D

    return CurveEditor, Slider2D, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Slider2D → Normal distribution

    Start simple: a single `Slider2D` puck picks one $(\mu, \sigma)$
    point and the panel on the right draws the corresponding
    $\mathcal{N}(\mu, \sigma)$ density. Drag the puck around and the
    density follows.

    There's no *path* through parameter space here — just one point
    at a time, one density. The next section swaps the puck for a
    `CurveEditor` so you can trace a whole curve through $(\mu,
    \sigma)$ space and see the family of densities it produces.
    """)
    return


@app.cell
def _(Slider2D, mo):
    puck = mo.ui.anywidget(
        Slider2D(
            x=0.0,
            y=1.0,
            x_bounds=(-3.0, 3.0),
            y_bounds=(0.2, 2.5),
            width=300,
            height=300,
        )
    )
    return (puck,)


@app.cell
def _(np, plt, puck):
    mu_pt = puck.x
    sigma_pt = max(puck.y, 1e-3)

    grid_pt = np.linspace(-6.0, 6.0, 400)
    density_pt = np.exp(-0.5 * ((grid_pt - mu_pt) / sigma_pt) ** 2) / (
        sigma_pt * np.sqrt(2 * np.pi)
    )
    standard_pt = np.exp(-0.5 * grid_pt**2) / np.sqrt(2 * np.pi)

    fig_pt, ax_pt = plt.subplots(figsize=(5, 4))
    ax_pt.plot(
        grid_pt,
        standard_pt,
        color="#2b3d4f",
        linewidth=1.2,
        linestyle="--",
        alpha=0.6,
        label=r"$\mathcal{N}(0, 1)$",
    )
    ax_pt.plot(
        grid_pt,
        density_pt,
        color="#d4451f",
        linewidth=2.2,
        label=f"$\\mu={mu_pt:.2f},\\ \\sigma={sigma_pt:.2f}$",
    )
    ax_pt.set_xlim(-6, 6)
    ax_pt.set_ylim(bottom=0)
    ax_pt.set_xlabel("x")
    ax_pt.set_ylabel("density")
    ax_pt.legend(loc="upper right", frameon=False)
    ax_pt.spines["top"].set_visible(False)
    ax_pt.spines["right"].set_visible(False)
    fig_pt.tight_layout()
    return fig_pt, mu_pt, sigma_pt


@app.cell
def _(fig_pt, mo, puck):
    mo.hstack([puck, fig_pt], gap=2, align="center", justify="start")
    return


@app.cell
def _(mo, mu_pt, sigma_pt):
    mo.callout(f"(μ, σ) = ({mu_pt:.3f}, {sigma_pt:.3f})")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CurveEditor → Normal distribution

    Treat the editor's chart space as the parameter space of a normal
    distribution: the x-axis is **$\mu$** (mean) and the y-axis is
    **$\sigma$** (standard deviation, kept positive). Drag the knots to
    trace a path through that space, then look at the panel on the right
    to see the family of $\mathcal{N}(\mu, \sigma)$ densities that path
    produces.

    The bold density is the current playback position
    `(editor.x, editor.y)`; the faded ones are sampled along the whole
    curve via `editor.samples`. Press play to watch the bold one sweep
    through the family.
    """)
    return


@app.cell
def _(CurveEditor, mo):
    editor = mo.ui.anywidget(
        CurveEditor(
            curve="natural",
            closed=False,
            loop=True,
            playing=False,
            width=340,
            height=340,
            x_bounds=(-3.0, 3.0),
            y_bounds=(0.2, 2.5),
            show_axes=True,
            duration_ms=8000,
            sync_throttle_ms=200,
            n_samples=60,
            points=[
                {"x": -2.0, "y": 0.4},
                {"x": -0.5, "y": 1.2},
                {"x": 1.0, "y": 0.6},
                {"x": 2.2, "y": 1.8},
            ],
        )
    )
    return (editor,)


@app.cell
def _(editor, np, plt):
    mu_now, sigma_now = editor.x, max(editor.y, 1e-3)

    grid = np.linspace(-6.0, 6.0, 400)


    def normal_pdf(x, mu, sigma):
        return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))


    fig, ax = plt.subplots(figsize=(5, 4))

    for sample in editor.samples:
        mu = sample["x"]
        sigma = max(sample["y"], 1e-3)
        ax.plot(grid, normal_pdf(grid, mu, sigma), color="#2b3d4f", alpha=0.08, linewidth=1)

    ax.plot(
        grid,
        normal_pdf(grid, mu_now, sigma_now),
        color="#d4451f",
        linewidth=2.2,
        label=f"$\\mu={mu_now:.2f},\\ \\sigma={sigma_now:.2f}$",
    )

    ax.set_xlim(-6, 6)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("x")
    ax.set_ylabel("density")
    ax.legend(loc="upper right", frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return (fig,)


@app.cell
def _(editor, fig, mo):
    mo.hstack([editor, fig], gap=2, align="center", justify="start")
    return


@app.cell
def _(editor, mo):
    mo.callout(
        f"t = {editor.t:.3f};  "
        f"current (μ, σ) = ({editor.x:.3f}, {max(editor.y, 1e-3):.3f});  "
        f"{len(editor.points)} knots;  {len(editor.samples)} samples"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Notes

    - $\sigma$ is clamped to a small positive minimum so the density stays
      well-defined even when a knot is dragged onto the $\sigma=0$ axis.
    - The faded family of densities comes straight from
      `editor.samples` — the browser samples the rendered curve at
      `n_samples=60` evenly spaced positions and ships the `(x, y)` pairs
      back, so adding or moving a knot updates the cloud immediately.
    - Press the play button on the editor to animate the bold density
      along the curve; raise `n_samples` for a denser cloud or lower it
      for a sparser one.
    """)
    return


if __name__ == "__main__":
    app.run()
