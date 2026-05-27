# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.5",
# ]
# ///
import marimo

__generated_with = "0.23.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import CurveEditor

    editor = mo.ui.anywidget(
        CurveEditor(
            curve="natural",
            loop=True,
            width=450,
            height=450,
            sync_throttle_ms=250,
            show_axes=True,
            x_bounds=(0.0, 10.0),
            y_bounds=(-1.0, 1.0),
            n_samples=120,
            points=[
                {"x": 0.0, "y": -0.6},
                {"x": 1.5, "y": -0.2},
                {"x": 3.5, "y": 0.6},
                {"x": 5.5, "y": -0.1},
                {"x": 7.8, "y": 0.75},
                {"x": 10.0, "y": 0.1},
            ],
        )
    )
    return editor, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## CurveEditor

    Edit chart-space knots and switch between D3 curve interpolators.
    Use the progress control to emit the current path position as `x` and
    `y`. Set `sync_throttle_ms` on construction to control how often
    playback syncs those values back to Python.

    This demo turns on **axes** (`show_axes=True`) so the custom
    `x_bounds=(0, 10)` and `y_bounds=(-1, 1)` are visible as tick labels.
    It also requests `n_samples=120` points along the rendered curve —
    the browser computes those after every render and pushes them back on
    the `samples` traitlet for Python to consume.
    """)
    return


@app.cell
def _(editor):
    editor
    return


@app.cell
def _(editor, mo):
    selected = (
        editor.points[editor.selected_index]
        if 0 <= editor.selected_index < len(editor.points)
        else None
    )
    mo.callout(
        f"curve = {editor.curve}; t = {editor.t:.3f}; "
        f"current = ({editor.x:.3f}, {editor.y:.3f}); {len(editor.points)} knots; "
        f"{len(editor.samples)} samples; "
        f"sync throttle = {editor.widget.sync_throttle_ms} ms; "
        f"selected = {selected if selected is not None else 'none'}"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Looping over `samples` in Python

    Because D3's interpolators live in the browser, Python used to have no
    easy way to ask "what does this curve actually look like between the
    knots?" The `samples` traitlet closes that gap — the browser samples
    the rendered SVG path at `n_samples` evenly spaced positions and ships
    the `(x, y)` pairs back. Drag a knot or switch the curve type and the
    numbers below update.
    """)
    return


@app.cell
def _(editor, mo):
    samples = editor.samples
    if len(samples) >= 2:
        pairs = list(zip(samples, samples[1:]))
        arc_length = sum(
            ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
            for a, b in pairs
        )
        ys = [point["y"] for point in samples]
        y_min, y_max = min(ys), max(ys)
        preview = ", ".join(f"({p['x']:.2f}, {p['y']:.2f})" for p in samples[:3])
        body = (
            f"- Approximate arc length: **{arc_length:.3f}**\n"
            f"- y range across the rendered curve: **[{y_min:.3f}, {y_max:.3f}]**\n"
            f"- First three samples: `{preview}`\n"
            f"- `len(editor.samples) == {len(samples)}`"
        )
    else:
        body = "_Waiting for the browser to render and push samples..._"
    mo.md(body)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Going further with numpy

    `samples` gives you a finite number of `(x, y)` pairs along the rendered
    curve. If you need values at arbitrary `x` positions in between — for
    example to evaluate the curve on the same grid as some other data — you
    can interpolate from those samples with numpy:

    ```python
    import numpy as np

    xs = np.array([p["x"] for p in editor.samples])
    ys = np.array([p["y"] for p in editor.samples])

    # For open curves the samples are already x-monotonic; for closed
    # curves you'll want to interpolate against arc length instead.
    finer_x = np.linspace(xs.min(), xs.max(), 1000)
    finer_y = np.interp(finer_x, xs, ys)
    ```

    `np.interp` does piecewise-linear interpolation between the rendered
    samples, so accuracy improves as you raise `n_samples`. For smoother
    interpolation between samples (e.g. cubic), reach for
    `scipy.interpolate.CubicSpline` instead.
    """)
    return


if __name__ == "__main__":
    app.run()
