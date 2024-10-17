import marimo

__generated_with = "0.9.10"
app = marimo.App()


@app.cell
def __(alt, df, df_base, mo, slider_2d):
    chart = (
        alt.Chart(df_base).mark_point(color="gray").encode(x="x", y="y") + 
        alt.Chart(df).mark_point().encode(x="x", y="y")
    ).properties(width=300, height=300)

    mo.vstack([
        mo.md("## `Slider2D` demo"),
        mo.md("This demo contains a two dimensional slider. The thinking is that sometimes you want to be able to make changes to two variables at the same time. The output is always standardized to the range of -1 to 1, but you can always use custom code to adapt this."),
        mo.hstack([slider_2d, chart])
    ])
    return (chart,)


@app.cell
def __(mo):
    from wigglystuff import Matrix

    matrix = mo.ui.anywidget(Matrix())
    matrix
    return Matrix, matrix


@app.cell
def __(mo):
    mo.md(r"""## Appendix with all supporting code""")
    return


@app.cell
def __():
    import altair as alt
    import marimo as mo
    import micropip
    import numpy as np
    import pandas as pd

    # await micropip.install("wigglystuff==0.1.1")
    return alt, micropip, mo, np, pd


@app.cell
def __(mo):
    from wigglystuff import Slider2D

    slider_2d = mo.ui.anywidget(Slider2D(width=300, height=300))
    return Slider2D, slider_2d


@app.cell
def __(np, pd, slider_2d):
    df = pd.DataFrame({
        "x": np.random.normal(slider_2d.x * 10, 1, 2000), 
        "y": np.random.normal(slider_2d.y * 10, 1, 2000)
    })
    return (df,)


@app.cell
def __(np, pd):
    df_base = pd.DataFrame({
        "x": np.random.normal(0, 1, 2000), 
        "y": np.random.normal(0, 1, 2000)
    })
    return (df_base,)


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
