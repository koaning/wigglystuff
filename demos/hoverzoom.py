# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.3.1",
#     "Pillow",
#     "matplotlib",
#     "numpy",
# ]
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import HoverZoom

    return HoverZoom, mo


@app.cell
def _():
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (800, 600), (30, 80, 120))
    draw = ImageDraw.Draw(img)
    for i in range(0, 800, 40):
        for j in range(0, 600, 40):
            color = ((i * 3) % 256, (j * 4) % 256, ((i + j) * 2) % 256)
            draw.ellipse([i, j, i + 30, j + 30], fill=color)
    return (img,)


@app.cell
def _(HoverZoom, img, mo):
    widget = mo.ui.anywidget(HoverZoom(img, zoom_factor=3.0, width=450))
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _():
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(42)
    n = 200
    x = rng.normal(0, 1, n)
    y = rng.normal(0, 1, n)
    labels = [f"p{i}" for i in range(n)]

    fig, ax = plt.subplots(figsize=(8, 6), dpi=200)
    ax.scatter(x, y, s=12, alpha=0.6)
    for xi, yi, label in zip(x, y, labels):
        ax.annotate(label, (xi, yi), fontsize=4, alpha=0.7, ha="center", va="bottom")
    ax.set_title("200 labeled points — hover to read the labels")
    fig.tight_layout()
    return (fig,)


@app.cell
def _(HoverZoom, fig, mo):
    chart_widget = mo.ui.anywidget(HoverZoom(fig, zoom_factor=4.0, width=500))
    return (chart_widget,)


@app.cell
def _(chart_widget):
    chart_widget
    return


if __name__ == "__main__":
    app.run()
