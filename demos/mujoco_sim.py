# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.19.4",
#     "wigglystuff==0.5.20",
#     "mujoco",
#     "numpy",
#     "imageio",
#     "imageio-ffmpeg",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A physics engine in marimo

    [MuJoCo](https://mujoco.org) is a physics engine. It can't render into a
    notebook directly, but it ships an **offscreen renderer** that draws
    frames without a window (no GPU or display needed). So the recipe is:
    **step the sim, render a frame after each step, encode the frames to an
    `.mp4`, and hand the bytes to `mo.video`.**

    The [`TangleSlider`](https://koaning.github.io/wigglystuff/) numbers in
    the sentence below are the sim's knobs. Drag any of them and marimo
    re-runs the simulation and regenerates the video.

    /// admonition | Runs on macOS, Linux, and molab
        type: note
    MuJoCo ships prebuilt wheels for macOS (arm64) and Linux, so this
    notebook installs with no compiler. It is a native extension, so it runs
    on a molab **server** rather than the in-browser WASM runtime that the
    pure-Python demos use.
    ///
    """)
    return


@app.cell(hide_code=True)
def _(bounce, drop_height, duration, gravity, mo, n_balls):
    mo.md(f"""
    Drop {n_balls} from a height of {drop_height}, under a gravity of
    {gravity}, with a bounciness of {bounce}. Then record {duration} of them
    raining down and settling in the video below.
    """)
    return


@app.cell(hide_code=True)
def _(mo, video_bytes):
    mo.video(src=video_bytes, controls=True, autoplay=True, muted=True, loop=True, width=520)
    return


@app.cell
def _():
    import marimo as mo

    from wigglystuff import TangleSlider

    return TangleSlider, mo


@app.cell
def _(TangleSlider, mo):
    n_balls = mo.ui.anywidget(
        TangleSlider(amount=15, min_value=1, max_value=40, step=1, digits=0, suffix=" balls")
    )
    drop_height = mo.ui.anywidget(
        TangleSlider(amount=3.0, min_value=1, max_value=8, step=0.5, digits=1, suffix=" m")
    )
    gravity = mo.ui.anywidget(
        TangleSlider(amount=9.8, min_value=0, max_value=25, step=0.1, digits=1, suffix=" m/s²")
    )
    bounce = mo.ui.anywidget(
        TangleSlider(amount=0.7, min_value=0, max_value=0.95, step=0.01, digits=2)
    )
    duration = mo.ui.anywidget(
        TangleSlider(amount=3.0, min_value=1, max_value=8, step=0.5, digits=1, suffix=" s")
    )
    return bounce, drop_height, duration, gravity, n_balls


@app.cell
def _():
    import random

    import numpy as np

    def build_scene(n_balls, drop_height, gravity, bounce):
        """Build an MJCF scene: `n_balls` colored spheres stacked above a floor."""
        # solref's damping ratio controls bounciness: 1.0 = dead stop, small = springy.
        dampratio = 1.0 - 0.9 * bounce
        rng = random.Random(0)  # deterministic layout as the knobs change
        bodies = []
        for i in range(n_balls):
            x, y = rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4)
            z = drop_height + i * 0.3
            r, g, b = rng.random(), rng.random(), rng.random()
            bodies.append(
                f'<body pos="{x:.3f} {y:.3f} {z:.3f}">'
                f"<freejoint/>"
                f'<geom type="sphere" size="0.12" rgba="{r:.2f} {g:.2f} {b:.2f} 0.55" '
                f'solref="0.01 {dampratio:.3f}"/>'
                f"</body>"
            )
        return f"""
        <mujoco>
          <option gravity="0 0 -{gravity}" timestep="0.002"/>
          <worldbody>
            <light pos="0 0 4" dir="0 0 -1"/>
            <geom name="floor" type="plane" size="5 5 0.1" rgba="0.8 0.8 0.85 1"/>
            {"".join(bodies)}
          </worldbody>
        </mujoco>
        """

    return build_scene, np


@app.cell
def _(build_scene, np):
    import mujoco

    def run_sim(
        n_balls, drop_height, gravity, bounce,
        n_frames=150, substeps=8, w=320, h=240,
    ):
        """Rain `n_balls` spheres onto a floor and capture each step as a frame."""
        model = mujoco.MjModel.from_xml_string(
            build_scene(n_balls, drop_height, gravity, bounce)
        )
        data = mujoco.MjData(model)
        renderer = mujoco.Renderer(model, height=h, width=w)
        try:
            cam = mujoco.MjvCamera()
            cam.azimuth, cam.elevation, cam.distance = 50, -25, 3.2
            cam.lookat[:] = [0, 0, 0.4]

            frames = []
            for _ in range(n_frames):
                for _ in range(substeps):
                    mujoco.mj_step(model, data)
                renderer.update_scene(data, cam)
                frames.append(renderer.render().copy())
            return np.stack(frames)
        finally:
            renderer.close()

    return (run_sim,)


@app.cell
def _():
    import pathlib
    import tempfile

    import imageio.v2 as imageio

    def encode_mp4(frames, fps=50):
        """Encode frames to a browser-friendly H.264 mp4 and return the bytes."""
        path = pathlib.Path(tempfile.gettempdir()) / "wigglystuff_mujoco.mp4"
        imageio.mimwrite(path, frames, fps=fps, macro_block_size=16)
        return path.read_bytes()

    return (encode_mp4,)


@app.cell
def _(bounce, drop_height, duration, encode_mp4, gravity, n_balls, run_sim):
    _fps = 50
    _frames = run_sim(
        n_balls=int(n_balls.amount),
        drop_height=drop_height.amount,
        gravity=gravity.amount,
        bounce=bounce.amount,
        n_frames=int(duration.amount * _fps),
    )
    video_bytes = encode_mp4(_frames, fps=_fps)
    return (video_bytes,)


if __name__ == "__main__":
    app.run()
