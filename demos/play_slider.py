import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from wigglystuff import PlaySlider

    slider = mo.ui.anywidget(
        PlaySlider(min_value=0, max_value=100, step=1, interval_ms=100, loop=True)
    )
    return mo, np, slider


@app.cell
def _(slider):
    slider


@app.cell
def _(mo):
    import matplotlib.pyplot as plt

    @mo.cache
    def make_plot(value):
        import numpy as np

        phase = value / 100 * 2 * np.pi
        x = np.linspace(0, 4 * np.pi, 300)

        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(x, np.sin(x + phase), color="#0ea5e9", linewidth=2)
        ax.fill_between(x, np.sin(x + phase), alpha=0.15, color="#0ea5e9")
        ax.set_ylim(-1.5, 1.5)
        ax.set_xlabel("x")
        ax.set_ylabel("sin(x + phase)")
        ax.set_title(f"phase = {phase:.2f} rad")
        plt.close(fig)
        return fig

    return (make_plot,)


@app.cell
def _(make_plot, slider):
    make_plot(slider.value.get("value", 0))


if __name__ == "__main__":
    app.run()
