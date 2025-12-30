import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import random

    import marimo as mo

    from wigglystuff import ThreeWidget

    random.seed(42)
    data = []
    for _ in range(900):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        hex_value = f"#{r:02x}{g:02x}{b:02x}"
        data.append(
            {
                "x": r / 255.0,
                "y": g / 255.0,
                "z": b / 255.0,
                "color": hex_value,
                "size": random.uniform(0.08, 0.2),
            }
        )

    widget = mo.ui.anywidget(
        ThreeWidget(
            data=data,
            width=640,
            height=420,
            show_grid=True,
            show_axes=True,
            axis_labels=["R", "G", "B"],
        )
    )
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
