# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.23.3",
#     "wigglystuff==0.5.30",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from wigglystuff import FormulaAnimation

    return FormulaAnimation, mo


@app.cell(hide_code=True)
def _(mo):
    theme = mo.ui.dropdown(options=["auto", "light", "dark"], value="light", label="Widget theme")
    mo.vstack(
        [
            mo.md(r"""
            # FormulaAnimation

            Step through a LaTeX derivation one line at a time. The current line
            sits centered, the previous line floats above it dimmed, and a short
            note explains each move. Use the **‹ / ›** buttons, or click the
            controls and use the **←/→** keys. A final *spotlight* step frames the
            finished formula on its own.
            """),
            theme,
        ],
        gap=0.5,
    )
    return (theme,)


@app.cell
def _(FormulaAnimation, mo, theme):
    anim = mo.ui.anywidget(
        FormulaAnimation(
            title="The abc-formula",
            steps=[
                {"tex": r"ax^2 + bx + c = 0", "note": "A quadratic equation, with a ≠ 0."},
                {
                    "tex": r"x^2 + \frac{b}{a}\,x + \frac{c}{a} = 0",
                    "note": "Make the leading coefficient 1.",
                },
                {"tex": r"x^2 + \frac{b}{a}\,x = -\frac{c}{a}", "note": "Get the x-terms alone."},
                {
                    "tex": r"\left(x + \frac{b}{2a}\right)^2 = \frac{b^2}{4a^2} - \frac{c}{a}",
                    "note": "Add (b/2a)² to both sides.",
                },
                {
                    "tex": r"\left(x + \frac{b}{2a}\right)^2 = \frac{b^2 - 4ac}{4a^2}",
                    "note": "One fraction over 4a².",
                },
                {
                    "tex": r"x + \frac{b}{2a} = \pm\frac{\sqrt{b^2 - 4ac}}{2a}",
                    "note": "Both signs survive the root.",
                },
                {"tex": r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}", "note": "The abc-formula."},
            ],
            theme=theme.value,
        )
    )
    anim
    return (anim,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can also scrub the animation from another cell by driving the `step`
    trait — for example with a slider.
    """)
    return


@app.cell
def _(anim, mo):
    scrub = mo.ui.slider(
        0,
        len(anim.steps),  # +1 slot for the spotlight step
        value=anim.step,
        label="step",
        full_width=True,
    )
    scrub
    return (scrub,)


@app.cell
def _(anim, scrub):
    anim.step = scrub.value
    return


if __name__ == "__main__":
    app.run()
