# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pillow",
#     "wigglystuff==0.5.18",
# ]
# ///

import marimo

__generated_with = "0.23.3"
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

    from wigglystuff import Matrix, Paint, WidgetDAG

    return Matrix, Paint, WidgetDAG, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Draw a digit, watch it convolve

    Scribble a digit on the `draw` canvas below. It is a live `Paint` node inside
    the DAG: your drawing is downsampled to a tiny array and pushed through two
    convolution kernels. Edit either kernel (they are live `Matrix` widgets) and
    the whole DAG recomputes. `WidgetDAG` lays the nodes out by edge-depth and
    draws the arrows for you.
    """)
    return


@app.cell
def _(Paint, mo):
    # The live drawing surface -- it IS the "draw" node embedded in the DAG below.
    # store_background=False keeps the canvas transparent, so the alpha channel of
    # the exported PNG is a clean ink mask (opaque where you drew, else transparent).
    paint = mo.ui.anywidget(Paint(width=260, height=260, color_picker=False, store_background=False))
    return (paint,)


@app.cell
def _(Matrix, mo):
    # Two kernels for the chained convolutions. Edit either to recompute.
    kernel = mo.ui.anywidget(Matrix(matrix=[[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
    kernel2 = mo.ui.anywidget(Matrix(matrix=[[1, 1, 1], [1, 1, 1], [1, 1, 1]]))
    return kernel, kernel2


@app.cell
def _(WidgetDAG, kernel, kernel2, mo, paint):
    import base64
    import io

    import numpy as np
    from PIL import Image

    def _img(a, width=110):
        a = np.asarray(a, dtype=float)
        lo, hi = float(a.min()), float(a.max())
        u8 = ((a - lo) / (hi - lo) * 255 if hi > lo else np.zeros_like(a)).astype("uint8")
        buf = io.BytesIO()
        Image.fromarray(u8).save(buf, format="PNG")
        src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        return mo.Html(
            f'<img src="{src}" style="width:{width}px;'
            f'image-rendering:pixelated;border:1px solid #ccc">'
        )

    def _convolve(a, k):
        from numpy.lib.stride_tricks import sliding_window_view

        kh, kw = k.shape
        return np.einsum("ijkl,kl->ij", sliding_window_view(a, (kh, kw)), k)

    # The drawing -> a 28x28 array. The alpha channel is the ink mask (bright
    # where you drew), which the convolutions sharpen and then blur.
    _arr = np.array(paint.get_pil().convert("RGBA").resize((28, 28)))[..., 3].astype(float)
    _out = _convolve(_arr, np.asarray(kernel.value["matrix"], dtype=float))
    _out2 = _convolve(_out, np.asarray(kernel2.value["matrix"], dtype=float))

    # draw ⊛ kernel -> conv ⊛ kernel2 -> conv2. The `draw` node IS the live Paint
    # widget and both kernel nodes ARE the live Matrix widgets, so drawing or
    # editing a kernel recomputes the DAG.
    WidgetDAG(
        nodes={
            "draw": paint,
            "kernel": kernel,
            "conv": _img(_out),
            "kernel2": kernel2,
            "conv2": _img(_out2),
        },
        edges=[
            ("draw", "conv"),
            ("kernel", "conv"),
            ("conv", "conv2"),
            ("kernel2", "conv2"),
        ],
    )
    return


if __name__ == "__main__":
    app.run()
