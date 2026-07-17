import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import CubeWidget

    return CubeWidget, mo


@app.cell
def _(CubeWidget, mo):
    cube = mo.ui.anywidget(
        CubeWidget(
            x_axis={"name": "Angle", "values": [0, 45, 90]},
            y_axis={"name": "Force", "values": [0, 50, 100]},
            z_axis={"name": "Time", "values": [0, 1, 2]},
        )
    )
    cube
    return (cube,)


@app.cell
def _(cube, mo):
    state = cube.value
    plane = state["plane"]["axis"] if state["plane"] else "-"
    line = state["line"]["axis"] if state["line"] else "-"
    point = state["point"]["axis"] if state["point"] else "-"
    mo.md(
        f'<div data-testid="cube-state">'
        f'locks={",".join(state["locked_order"])}; '
        f'x={state["axis_values"]["x"]}; '
        f'y={state["axis_values"]["y"]}; '
        f'z={state["axis_values"]["z"]}; '
        f'plane={plane}; line={line}; point={point}'
        "</div>"
    )
    return


@app.cell
def _(cube, mo):
    def update_x_axis(_):
        cube.widget.x_axis = {
            "name": "Bearing",
            "values": [0, 90, 180],
        }

    mo.ui.button(label="Update X axis", on_click=update_x_axis)
    return


if __name__ == "__main__":
    app.run()
