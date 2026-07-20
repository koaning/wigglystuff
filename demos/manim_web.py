# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.16",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import ManimWeb

    return ManimWeb, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ManimWeb

    `ManimWeb` runs a [manim-web](https://github.com/maloyan/manim-web) scene
    directly in the notebook. The engine is loaded from a CDN and your
    JavaScript runs with `manim`, `container`, `width`, `height`, and `model`
    in scope.

    The whole point of this is that you can add videos that help explain the algorithm. You can host the video with JS inside the notebook or link out to a file hosted elsewhere.
    """)
    return


@app.cell
def _(ManimWeb):
    scene = """
        const player = new manim.Player(container, {
            width,
            height,
            autoPlay: true,
            backgroundColor: manim.BLACK,
        });

        player.sequence(async (scene) => {
            const circle = new manim.Circle({ radius: 1.5, color: manim.BLUE, fillOpacity: 1 });
            await scene.play(new manim.Create(circle));
            await scene.wait(0.5);

            const square = new manim.Square({ sideLength: 3, color: manim.RED, fillOpacity: 1 });
            await scene.play(new manim.Transform(circle, square));
            await scene.play(new manim.Indicate(circle));

            const triangle = new manim.Triangle({ color: manim.GREEN, fillOpacity: 1 });
            triangle.scale(2);
            await scene.play(new manim.Transform(circle, triangle));
            await scene.play(new manim.Rotate(circle, { angle: Math.PI }));
            await scene.play(new manim.FadeOut(circle));

            const circle2 = new manim.Circle({ radius: 1, color: manim.YELLOW, fillOpacity: 1 });
            await scene.play(new manim.FadeIn(circle2));
            await scene.wait(1);
        });
    """

    ManimWeb(code=scene, width=800, height=450)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The really neat thing is that you can host these via the web too!
    """)
    return


@app.cell
def _(ManimWeb):
    ManimWeb("https://gist.githubusercontent.com/koaning/d10cb73fafe5e1355237d17fa7b5d5cf/raw/993326194d08dc2d8ddb9131927a243b344642df/demo.js")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Not just videos: static charts and 3D

    You don't need animation. Plot functions on an `Axes` and `add()` them
    without calling `play()` for a **static chart**, or reach for a
    `ThreeDScene` (with `Sphere`, `Cube`, `ThreeDAxes`, …) for **3D**.
    """)
    return


@app.cell
def _(ManimWeb):
    chart = """
        const scene = new manim.Scene(container, {
            width, height, backgroundColor: manim.BLACK,
        });

        const axes = new manim.Axes({
            xRange: [-10, 10, 2],
            yRange: [-1.5, 1.5, 0.5],
            xLength: 11,
            yLength: 5,
            axisConfig: { color: manim.GREY_B },
            tips: false,
        });

        const sinGraph = axes.plot((x) => Math.sin(x), { color: manim.BLUE });
        const cosGraph = axes.plot((x) => Math.cos(x), { color: manim.RED });

        // No play() -> a static chart.
        scene.add(axes, axes.getAxisLabels(), sinGraph, cosGraph);
    """

    ManimWeb(code=chart, width=720, height=440)
    return


@app.cell
def _(ManimWeb):
    scene_3d = """
        const scene = new manim.ThreeDScene(container, {
            width,
            height,
            backgroundColor: manim.WHITE,
            phi: 75 * Math.PI / 180,
            theta: -45 * Math.PI / 180,
            distance: 14,  // zoomed out enough that the top z label stays in frame
            fov: 30,
            enableOrbitControls: true,  // drag to rotate
            orbitControlsUp: "z",
        });

        const axes = new manim.ThreeDAxes({
            xRange: [-3, 3, 1], yRange: [-3, 3, 1], zRange: [-3, 3, 1],
            xLength: 6, yLength: 6, zLength: 6, showLabels: true,
            axisColor: "#444444",  // axes default to white; darken for white bg
        });
        // labels are white by default too, so recolor them to match the axes
        axes.getXLabel()?.setColor("#444444");
        axes.getYLabel()?.setColor("#444444");
        axes.getZLabel()?.setColor("#444444");
        const sphere = new manim.Sphere({ radius: 1.5, color: manim.BLUE });
        scene.add(axes, sphere);
        scene.wait(Infinity);  // keep the render loop alive for orbit controls
    """

    ManimWeb(code=scene_3d, width=640, height=500)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
