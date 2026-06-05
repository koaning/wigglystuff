# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.4",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    from wigglystuff import AttractorWidget, TangleSlider

    return AttractorWidget, TangleSlider, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # AttractorWidget

    GPU-accelerated 2D iterative-map attractor renderer. The default
    `phase` theme uses the per-iteration-distance coloring from Ricky
    Reusser's
    [Clifford and de Jong Attractors: Revised coloring](https://observablehq.com/@rreusser/clifford-and-de-jong-attractors-revised-coloring).
    Switch the theme to `magma`, `viridis`, `inferno`, `plasma`, or
    `grayscale` to fall back to a density-only LUT — those modes ignore
    `color_speed` / `color_phase`. **Drag the canvas to pan, scroll to
    zoom.**
    """)
    return


@app.cell
def _(TangleSlider, mo):
    formula = mo.ui.dropdown(
        options=["clifford", "de_jong"], value="clifford", label="formula"
    )
    a = mo.ui.anywidget(
        TangleSlider(min_value=-3.0, max_value=3.0, step=0.01, amount=-1.7, digits=2)
    )
    b = mo.ui.anywidget(
        TangleSlider(min_value=-3.0, max_value=3.0, step=0.01, amount=1.8, digits=2)
    )
    c = mo.ui.anywidget(
        TangleSlider(min_value=-3.0, max_value=3.0, step=0.01, amount=-1.9, digits=2)
    )
    d = mo.ui.anywidget(
        TangleSlider(min_value=-3.0, max_value=3.0, step=0.01, amount=-0.4, digits=2)
    )
    colormap = mo.ui.dropdown(
        options=["phase", "magma", "viridis", "inferno", "plasma", "grayscale"],
        value="phase",
        label="theme",
    )
    color_speed = mo.ui.anywidget(
        TangleSlider(min_value=0.0, max_value=1.0, step=0.01, amount=0.22, digits=2)
    )
    color_phase = mo.ui.anywidget(
        TangleSlider(min_value=0.0, max_value=360.0, step=1.0, amount=180.0, digits=0)
    )
    background = mo.ui.dropdown(
        options=["black", "white"], value="black", label="background"
    )
    return a, b, background, c, color_phase, color_speed, colormap, d, formula


@app.cell
def _(AttractorWidget, mo):
    attractor = mo.ui.anywidget(
        AttractorWidget.clifford(
            width=500,
            height=500,
            n_points=100_000,
            iterations_per_frame=2,
        )
    )
    return (attractor,)


@app.cell
def _(attractor, formula):
    # Marimo re-runs any cell that references `attractor` whenever *any* of
    # its sync traitlets change — including `view` updates that come back
    # from JS-side pan/zoom. Guarding each assignment so it only fires on
    # an actual change keeps the user's gesture from being clobbered.
    if formula.value == "clifford":
        new_x = "sin(a*y) + c*cos(a*x)"
        new_y = "sin(b*x) + d*cos(b*y)"
        new_view = (-2.5, 2.5, -2.5, 2.5)
    else:
        new_x = "sin(a*y) - cos(b*x)"
        new_y = "sin(c*x) - cos(d*y)"
        new_view = (-2.2, 2.2, -2.2, 2.2)
    if attractor.x_expr != new_x:
        attractor.x_expr = new_x
        attractor.y_expr = new_y
        attractor.view = new_view
    return


@app.cell
def _(a, attractor, b, background, c, color_phase, color_speed, colormap, d):
    new_params = {"a": a.amount, "b": b.amount, "c": c.amount, "d": d.amount}
    if attractor.params != new_params:
        attractor.params = new_params
    if attractor.colormap != colormap.value:
        attractor.colormap = colormap.value
    if attractor.color_speed != color_speed.amount:
        attractor.color_speed = color_speed.amount
    if attractor.color_phase != color_phase.amount:
        attractor.color_phase = color_phase.amount
    if attractor.background != background.value:
        attractor.background = background.value
    return


@app.cell(hide_code=True)
def _(
    a,
    attractor,
    b,
    background,
    c,
    color_phase,
    color_speed,
    colormap,
    d,
    formula,
    mo,
):
    mo.vstack(
        [
            mo.md(
                f"""
                {formula} &nbsp;&nbsp; a = {a} &nbsp; b = {b} &nbsp; c = {c} &nbsp; d = {d}

                {colormap} &nbsp;&nbsp; color_speed = {color_speed} &nbsp;&nbsp; color_phase = {color_phase}° &nbsp;&nbsp; {background}
                """
            ),
            attractor,
        ]
    )
    return


@app.cell
def _(attractor):
    attractor.value
    return


if __name__ == "__main__":
    app.run()
