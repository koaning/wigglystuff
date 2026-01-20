import marimo

__generated_with = "0.18.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartPuck

    return ChartPuck, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md("## Single Puck")
    return


@app.cell
def _(ChartPuck, np, plt):
    # Create a scatter plot
    np.random.seed(42)
    x_data = np.random.randn(50)
    y_data = np.random.randn(50)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x_data, y_data, alpha=0.6)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Drag the puck to select coordinates")
    ax.grid(True, alpha=0.3)

    puck = ChartPuck(fig, x=0, y=0)
    plt.close(fig)
    return ax, fig, puck, x_data, y_data


@app.cell
def _(mo, puck):
    widget = mo.ui.anywidget(puck)
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget):
    mo.callout(f"Selected position: x = {widget.x[0]:.3f}, y = {widget.y[0]:.3f}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("## Multiple Pucks")
    return


@app.cell
def _(ChartPuck, np, plt):
    # Create a scatter plot with multiple pucks
    np.random.seed(123)
    x_multi = np.random.randn(50)
    y_multi = np.random.randn(50)

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.scatter(x_multi, y_multi, alpha=0.6)
    ax2.set_xlim(-3, 3)
    ax2.set_ylim(-3, 3)
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_title("Drag any puck - closest one will move")
    ax2.grid(True, alpha=0.3)

    multi_puck = ChartPuck(
        fig2,
        x=[-1.5, 0, 1.5],
        y=[-1.5, 0, 1.5],
        puck_color="#2196f3",
    )
    plt.close(fig2)
    return ax2, fig2, multi_puck, x_multi, y_multi


@app.cell
def _(mo, multi_puck):
    multi_widget = mo.ui.anywidget(multi_puck)
    return (multi_widget,)


@app.cell
def _(multi_widget):
    multi_widget
    return


@app.cell
def _(mo, multi_widget):
    positions = [
        f"Puck {i+1}: ({x:.2f}, {y:.2f})"
        for i, (x, y) in enumerate(zip(multi_widget.x, multi_widget.y))
    ]
    mo.callout("\n".join(positions))
    return (positions,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("## Dynamic Chart Updates")
    return


@app.cell
def _(np):
    np.random.seed(42)
    dynamic_data_x = np.random.randn(50)
    dynamic_data_y = np.random.randn(50)
    return dynamic_data_x, dynamic_data_y


@app.cell
def _(ChartPuck, dynamic_data_x, dynamic_data_y):
    def draw_with_crosshairs(ax, x, y):
        ax.scatter(dynamic_data_x, dynamic_data_y, alpha=0.6)
        ax.axvline(x, color="red", linestyle="--", alpha=0.7)
        ax.axhline(y, color="red", linestyle="--", alpha=0.7)
        ax.set_title(f"Position: ({x:.2f}, {y:.2f})")
        ax.grid(True, alpha=0.3)

    dynamic_puck = ChartPuck.from_callback(
        draw_fn=draw_with_crosshairs,
        x_bounds=(-3, 3),
        y_bounds=(-3, 3),
        figsize=(6, 6),
        x=0,
        y=0,
        puck_color="#4caf50",
    )
    return draw_with_crosshairs, dynamic_puck


@app.cell
def _(dynamic_puck, mo):
    dynamic_widget = mo.ui.anywidget(dynamic_puck)
    return (dynamic_widget,)


@app.cell
def _(dynamic_widget):
    dynamic_widget
    return


@app.cell
def _(dynamic_widget, mo):
    mo.callout(
        f"Dynamic position: x = {dynamic_widget.x[0]:.3f}, y = {dynamic_widget.y[0]:.3f}"
    )
    return


if __name__ == "__main__":
    app.run()
