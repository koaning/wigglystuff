# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "pillow",
#     "wigglystuff==0.5.17",
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
    ## Fancier: pixel art from PIL images

    `FramePlayer` takes PIL images directly, so any drawing library works. Below
    is a set of recursive concentric squares drawn pixel-by-pixel with `PIL` on a
    small grid and scaled up with nearest-neighbour for a chunky, pixel-y look. A
    gentle lightness wave flows inward, and since it cycles over a full period the
    loop is seamless.
    """)
    return


@app.cell
def _():
    import math

    from PIL import Image

    def make_art_frames(n_frames=48, grid=44, scale=9):
        frames = []
        for f in range(n_frames):
            t = f / n_frames  # 0 -> 1 across the loop
            img = Image.new("RGB", (grid, grid), (30, 36, 44))
            px = img.load()

            def rings(lo, hi, depth):
                if lo > hi:
                    return
                # calm single-hue teal with a soft lightness wave flowing inward
                light = 0.56 + 0.16 * math.sin(2 * math.pi * (depth * 0.11 - t))
                color = (
                    int(255 * light * 0.62),
                    int(255 * light * 0.92),
                    int(255 * light * 0.86),
                )
                for i in range(lo, hi + 1):
                    px[i, lo] = color
                    px[i, hi] = color
                    px[lo, i] = color
                    px[hi, i] = color
                rings(lo + 1, hi - 1, depth + 1)

            rings(0, grid - 1, 0)
            # nearest-neighbour upscale keeps the crisp, pixel-y edges
            frames.append(img.resize((grid * scale, grid * scale), Image.NEAREST))
        return frames

    return (make_art_frames,)


@app.cell
def _(FramePlayer, make_art_frames, mo):
    art_player = mo.ui.anywidget(
        FramePlayer(make_art_frames(), interval_ms=90, loop=True)
    )
    art_player
    return


if __name__ == "__main__":
    app.run()
