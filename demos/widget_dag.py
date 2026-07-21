# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "mohtml",
#     "numpy",
#     "pillow",
#     "wigglystuff==0.5.21",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    # Prefer the local checkout so this demo tracks the in-repo WidgetDAG even
    # before it lands in a published wigglystuff release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import Paint, WidgetDAG

    return Paint, WidgetDAG, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Draw a digit, watch it convolve

    Scribble a digit on the `paint` canvas below. It is a live `Paint` node inside
    the DAG: your drawing is downsampled to a tiny array and pushed through two
    convolution kernels. Edit either kernel (they are live `mo.ui.matrix` editors)
    and the whole DAG recomputes. The `angle` node is a plain `mo.ui.slider` -- any
    marimo UI element works as a node -- and dragging it re-rotates the digit
    before it is convolved.

    Each node lives in its own cell, so `WidgetDAG.from_widgets([...])` reads
    marimo's dataflow graph to place the nodes by edge-depth and draw the arrows
    for you -- no `edges=` list to spell out by hand.
    """)
    return


@app.cell
def _(angle, conv, conv2, kernel, kernel2, paint):
    [conv, angle, paint, kernel, kernel2, conv2]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Above is "meh", we can do better below.
    """)
    return


@app.cell
def _(WidgetDAG, angle, conv, conv2, kernel, kernel2, paint):
    WidgetDAG.from_widgets([paint, angle, kernel, conv, kernel2, conv2])
    return


@app.cell
def _(Paint, mo):
    # The live drawing surface -- it IS the "paint" node embedded in the DAG below.
    # store_background=False keeps the canvas transparent, so the alpha channel of
    # the exported PNG is a clean ink mask (opaque where you drew, else transparent).
    paint = mo.ui.anywidget(Paint(width=260, height=260, color_picker=False, store_background=False))
    return (paint,)


@app.cell
def _(mo):
    # First convolution kernel -- a native mo.ui.matrix editor (drag an entry to
    # change it). It lives in its own cell so the DAG can wire it to `conv` only.
    kernel = mo.ui.matrix([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return (kernel,)


@app.cell
def _(mo):
    # Second kernel, in its own cell too -- it feeds `conv2`.
    kernel2 = mo.ui.matrix([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
    return (kernel2,)


@app.cell
def _(mo):
    # A plain mo.ui.slider -- it lives in the DAG as a node just like the widgets
    # above, and rotates the drawn digit before it is convolved.
    angle = mo.ui.slider(-180, 180, value=0, step=5, label="rotate°", show_value=True)
    return (angle,)


@app.cell
def _():
    # Shared helpers -- exported (no leading underscore) so the two convolution
    # cells below can both use them.
    import base64
    import io

    import numpy as np
    from mohtml import img
    from PIL import Image

    def to_img(a, width=110):
        a = np.asarray(a, dtype=float)
        lo, hi = float(a.min()), float(a.max())
        u8 = ((a - lo) / (hi - lo) * 255 if hi > lo else np.zeros_like(a)).astype("uint8")
        buf = io.BytesIO()
        Image.fromarray(u8).save(buf, format="PNG")
        src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        return img(
            src=src,
            style=f"width:{width}px;image-rendering:pixelated;border:1px solid #ccc",
        )

    def convolve(a, k):
        from numpy.lib.stride_tricks import sliding_window_view

        kh, kw = k.shape
        return np.einsum("ijkl,kl->ij", sliding_window_view(a, (kh, kw)), k)

    return convolve, np, to_img


@app.cell
def _(angle, convolve, kernel, np, paint, to_img):
    # The drawing -> rotate by the slider -> a 28x28 array -> convolve with `kernel`.
    # The alpha channel is the ink mask (bright where you drew); rotating the
    # full-res PIL (transparent fill) keeps that mask clean. `conv` is the image
    # node; `out1` is the array the next cell picks up (that reference is the edge
    # `conv -> conv2` the DAG draws).
    _pil = paint.get_pil().convert("RGBA").rotate(angle.value)
    _arr = np.array(_pil.resize((28, 28)))[..., 3].astype(float)
    out1 = convolve(_arr, np.asarray(kernel.value, dtype=float))
    conv = to_img(out1)
    return conv, out1


@app.cell
def _(convolve, kernel2, np, out1, to_img):
    # Second convolution: `out1` (from the cell above) blurred by `kernel2`.
    out2 = convolve(out1, np.asarray(kernel2.value, dtype=float))
    conv2 = to_img(out2)
    return (conv2,)


if __name__ == "__main__":
    app.run()
