# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.16",
# ]
# ///

import marimo

__generated_with = "0.23.3"
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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
