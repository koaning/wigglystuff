# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.2.21",
# ]
# ///
import marimo

__generated_with = "0.18.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import ColorPicker

    picker = mo.ui.anywidget(ColorPicker(color="#0ea5e9"))
    return mo, picker


@app.cell
def _(picker):
    picker
    return


@app.cell
def _(mo, picker):
    r, g, b = picker.rgb

    mo.vstack(
        [
            mo.md(f"You picked **{picker.color}** which is **RGB {r}, {g}, {b}**."),
            mo.md(
                f"<div style='width:96px;height:96px;border-radius:0.75rem;"
                f"border:1px solid #d4d4d8;background:{picker.color};'></div>"
            ),
            mo.md("Hex labels are shown by default. Set `show_label=False` to hide them."),
        ]
    )
    return


@app.cell
def _(mo, picker):
    import random


    def randomize(_):
        picker.color = f"#{random.randint(0, 0xFFFFFF):06x}"


    mo.ui.button(label="Surprise me", on_click=randomize)
    return


if __name__ == "__main__":
    app.run()
