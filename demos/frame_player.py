# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "pillow",
#     "wigglystuff==0.5.16",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # FramePlayer

    Hook a sequence of images up to play/pause/loop controls and watch it
    render inline as a looping "video" — no second cell that reads a slider
    value and re-renders.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np

    from wigglystuff import FramePlayer

    return FramePlayer, mo, np


@app.cell
def _(np):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def make_frames(n=40):
        frames = []
        x = np.linspace(0, 4 * np.pi, 300)
        for phase in np.linspace(0, 2 * np.pi, n, endpoint=False):
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(x, np.sin(x + phase), color="#0ea5e9", linewidth=2)
            ax.fill_between(x, np.sin(x + phase), alpha=0.15, color="#0ea5e9")
            ax.set_ylim(-1.5, 1.5)
            ax.set_title("A travelling sine wave")
            plt.close(fig)
            frames.append(fig)
        return frames

    return (make_frames,)


@app.cell
def _(FramePlayer, make_frames, mo):
    player = mo.ui.anywidget(
        FramePlayer(make_frames(), interval_ms=80, loop=True)
    )
    player
    return (player,)


@app.cell(hide_code=True)
def _(mo, player):
    mo.md(f"""
    Currently showing frame **{player.value.get('value', 0)}**.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Fancier: generative art from PIL images

    `FramePlayer` takes PIL images directly, so any drawing library works. Below
    is a phyllotaxis "sunflower" spiral drawn with `PIL.ImageDraw` — each frame
    spins the pattern and cycles the hue, and because both wrap over a full turn
    the loop is seamless.
    """)
    return


@app.cell
def _():
    import colorsys
    import math

    from PIL import Image, ImageDraw

    def make_art_frames(n_frames=48, size=420, n_dots=520):
        golden_angle = math.pi * (3 - math.sqrt(5))  # ~137.5°
        center = size / 2
        scale = (size * 0.46) / math.sqrt(n_dots)
        frames = []
        for f in range(n_frames):
            t = f / n_frames  # 0 -> 1 across the loop
            img = Image.new("RGB", (size, size), (11, 14, 20))
            draw = ImageDraw.Draw(img)
            spin = t * 2 * math.pi
            for i in range(n_dots):
                r = scale * math.sqrt(i)
                theta = i * golden_angle + spin
                x = center + r * math.cos(theta)
                y = center + r * math.sin(theta)
                hue = (i / n_dots + t) % 1.0
                cr, cg, cb = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
                dot = 1.5 + 5.5 * (i / n_dots)  # grow toward the rim
                draw.ellipse(
                    [x - dot, y - dot, x + dot, y + dot],
                    fill=(int(cr * 255), int(cg * 255), int(cb * 255)),
                )
            frames.append(img)
        return frames

    return (make_art_frames,)


@app.cell
def _(FramePlayer, make_art_frames, mo):
    art_player = mo.ui.anywidget(
        FramePlayer(make_art_frames(), interval_ms=60, loop=True)
    )
    art_player
    return


if __name__ == "__main__":
    app.run()
