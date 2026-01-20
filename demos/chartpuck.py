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


if __name__ == "__main__":
    app.run()
