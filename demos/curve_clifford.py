# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "wigglystuff==0.5.5",
# ]
# ///
import marimo

__generated_with = "0.23.7"
app = marimo.App()


@app.cell
def _():
    import math
    from functools import lru_cache

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    from wigglystuff import CurveEditor, Slider2D

    return CurveEditor, Slider2D, lru_cache, math, mo, np, plt


@app.cell
def _(lru_cache, math, np):
    @lru_cache(maxsize=32)
    def compute_attractor(a, b, c, d, n_iter):
        xs = [0.0] * n_iter
        ys = [0.0] * n_iter
        xs[0], ys[0] = 0.1, 0.0
        sin, cos = math.sin, math.cos
        for i in range(1, n_iter):
            xs[i] = sin(a * ys[i - 1]) - cos(b * xs[i - 1])
            ys[i] = sin(c * xs[i - 1]) - cos(d * ys[i - 1])
        return np.asarray(xs), np.asarray(ys)

    return (compute_attractor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CurveEditor → de Jong attractor

    A [Peter de Jong attractor](https://en.wikipedia.org/wiki/List_of_chaotic_maps)
    is a 2D recurrence with four real parameters $(a, b, c, d)$:

    $$
    \begin{aligned}
    x_{n+1} &= \sin(a \cdot y_n) - \cos(b \cdot x_n) \\
    y_{n+1} &= \sin(c \cdot x_n) - \cos(d \cdot y_n)
    \end{aligned}
    $$

    All four parameters play symmetric roles inside the trig functions,
    and most of the $[-3, 3]^4$ hypercube produces a recognisably
    strange attractor — much fewer dead zones than Clifford's variant.

    This demo splits the four parameters across two widgets:

    - **`CurveEditor`** — the playback position along the curve,
      `(editor.x, editor.y)`, drives $(a, b)$ live. Press play and it
      sweeps from knot to knot.
    - **`Slider2D`** — a separate 2D puck supplies $(c, d)$.
    """)
    return


@app.cell
def _(CurveEditor, Slider2D, mo):
    editor = mo.ui.anywidget(
        CurveEditor(
            curve="natural",
            closed=False,
            loop=True,
            playing=False,
            width=260,
            height=260,
            x_bounds=(-3.0, 3.0),
            y_bounds=(-3.0, 3.0),
            show_axes=True,
            duration_ms=8000,
            sync_throttle_ms=200,
            n_samples=120,
            points=[
                {"x": 1.4, "y": -2.3},
                {"x": -2.0, "y": -2.0},
            ],
        )
    )
    cd_picker = mo.ui.anywidget(
        Slider2D(
            x=2.4, y=-2.1,
            x_bounds=(-3.0, 3.0), y_bounds=(-3.0, 3.0),
            width=180, height=180,
        )
    )
    return cd_picker, editor


@app.cell
def _(cd_picker, compute_attractor, editor, plt):
    a, b = editor.x, editor.y
    c, d = cd_picker.x, cd_picker.y

    xs, ys = compute_attractor(a, b, c, d, 200_000)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(xs, ys, s=0.05, alpha=0.15, color="#2b3d4f", linewidths=0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return a, b, c, d, fig


@app.cell
def _(cd_picker, editor, fig, mo):
    cd_block = mo.vstack(
        [mo.md("**(c, d) puck**"), cd_picker], gap=0.5, align="center",
    )
    mo.hstack([editor, cd_block, fig], gap=2, align="center")
    return


@app.cell
def _(a, b, c, d, editor, mo):
    mo.callout(
        f"t = {editor.t:.3f};  (a, b) = ({a:.3f}, {b:.3f})  "
        f"(from curve);  (c, d) = ({c:.3f}, {d:.3f})  (puck)"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Parameter sets worth trying

    To freeze the attractor at a known nice shape, drag **point 0** to
    $(a, b)$, drag the **puck** to $(c, d)$, and either pause the editor
    or drop **point 1** on top of point 0:

    - $(1.4, -2.3, 2.4, -2.1)$ — the canonical de Jong shape.
    - $(-2.0, -2.0, -1.2, 2.0)$ — woven scrollwork.
    - $(-2.7, -0.09, -0.86, -2.2)$ — looped ribbon.
    - $(2.01, -2.53, 1.61, -0.33)$ — dense moth.

    With only two knots the curve is a straight segment. Double-click
    the canvas to add more knots — $(a, b)$ then traces the whole drawn
    shape while $(c, d)$ stays put.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Render a higher-resolution video

    The frames of the morph come straight from the editor's new
    `samples` traitlet — D3 in the browser hands Python `n_samples=120`
    densely interpolated `(x, y)` pairs along the rendered curve. Each
    sample becomes one frame's `(a, b)`, while `(c, d)` stays fixed at
    the current `Slider2D` puck position. The frame list is palindromed
    (forward then back) so the video loops without a visual jump. Click
    the link that appears under the progress bar to open the saved file.
    """)
    return


@app.cell
def _(mo):
    n_iter_slider = mo.ui.slider(
        start=200_000, stop=1_500_000, step=100_000, value=600_000,
        label="iterations per frame", show_value=True,
    )
    dpi_slider = mo.ui.slider(
        start=72, stop=200, step=8, value=144,
        label="dpi", show_value=True,
    )
    render_btn = mo.ui.run_button(label="Render video", kind="success")
    mo.hstack([n_iter_slider, dpi_slider, render_btn], justify="start", gap=2)
    return dpi_slider, n_iter_slider, render_btn


@app.cell
def _(
    cd_picker,
    compute_attractor,
    dpi_slider,
    editor,
    mo,
    n_iter_slider,
    np,
    plt,
    render_btn,
):
    import shutil
    from pathlib import Path

    import matplotlib.animation as animation

    mo.stop(
        not render_btn.value,
        mo.md(
            "_Adjust the controls and click_ **Render video** _to start. "
            "Renders use the editor's current `samples` list and the "
            "current `(c, d)` puck position._"
        ),
    )

    samples = editor.samples
    mo.stop(
        len(samples) < 2,
        mo.md("_Waiting for the editor to push samples — drag a point and try again._"),
    )

    c_fixed, d_fixed = cd_picker.x, cd_picker.y

    n_iter = int(n_iter_slider.value)
    dpi = int(dpi_slider.value)
    n_frames = len(samples)

    # Palindrome the frame order so the loop has no jump: (a, b) sweeps
    # along the curve to point 1 and back to point 0.
    frame_indices = list(range(n_frames)) + list(range(n_frames - 2, 0, -1))
    n_render = len(frame_indices)

    # Auto-fit axes from a few representative frames.
    probe_indices = (0, n_frames // 2, n_frames - 1)
    lo, hi = float("inf"), float("-inf")
    with mo.status.progress_bar(
        total=len(probe_indices),
        title="Probing bounds",
    ) as _probe_bar:
        for idx in probe_indices:
            s_a = samples[idx]
            xs_p, ys_p = compute_attractor(
                s_a["x"], s_a["y"], c_fixed, d_fixed, n_iter
            )
            lo = min(lo, float(xs_p.min()), float(ys_p.min()))
            hi = max(hi, float(xs_p.max()), float(ys_p.max()))
            _probe_bar.update()
    margin = 0.1 * (hi - lo)
    lo, hi = lo - margin, hi + margin

    _fig, _ax = plt.subplots(figsize=(6, 6))
    _ax.set_aspect("equal")
    _ax.set_xticks([])
    _ax.set_yticks([])
    for _spine in _ax.spines.values():
        _spine.set_visible(False)
    _ax.set_xlim(lo, hi)
    _ax.set_ylim(lo, hi)
    _scat = _ax.scatter([], [], s=0.05, alpha=0.15, color="#2b3d4f", linewidths=0)

    def _update(frame):
        i = frame_indices[frame]
        s_a = samples[i]
        xs_f, ys_f = compute_attractor(s_a["x"], s_a["y"], c_fixed, d_fixed, n_iter)
        _scat.set_offsets(np.column_stack([xs_f, ys_f]))
        return (_scat,)

    _anim = animation.FuncAnimation(_fig, _update, frames=n_render, blit=True)

    with mo.status.progress_bar(
        total=n_render,
        title="Rendering frames",
        subtitle=f"{n_iter:,} iterations per frame (palindrome loop)",
    ) as _render_bar:
        def _on_frame(current, total):
            _render_bar.update()

        if shutil.which("ffmpeg"):
            out_path = Path("dejong_morph.mp4")
            _anim.save(
                str(out_path), fps=24, dpi=dpi, writer="ffmpeg",
                progress_callback=_on_frame,
            )
        else:
            out_path = Path("dejong_morph.gif")
            _anim.save(
                str(out_path), fps=15, dpi=dpi,
                writer=animation.PillowWriter(fps=15),
                progress_callback=_on_frame,
            )
    plt.close(_fig)

    size_mb = out_path.stat().st_size / 1_048_576
    mo.md(
        f"[Open {out_path.name}]({out_path.resolve().as_uri()}) — "
        f"{size_mb:.1f} MB, {n_render} frames, {n_iter:,} iterations/frame, "
        f"dpi {dpi}."
    )
    return


if __name__ == "__main__":
    app.run()
