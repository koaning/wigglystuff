

import marimo

__generated_with = "0.11.26"
app = marimo.App()


@app.cell
def _(alt, df, df_base, mo, slider_2d):
    chart = (
        alt.Chart(df_base).mark_point(color="gray").encode(x="x", y="y") + 
        alt.Chart(df).mark_point().encode(x="x", y="y")
    ).properties(width=300, height=300)

    mo.vstack([
        mo.md("""
    ## `Slider2D` demo

    ```python
    from wigglystuff import Slider2D

    slider_2d = Slider2D(width=300, height=300)
    ```

    This demo contains a two dimensional slider. The thinking is that sometimes you want to be able to make changes to two variables at the same time. The output is always standardized to the range of -1 to 1, but you can always use custom code to adapt this."""),
        mo.hstack([slider_2d, chart])
    ])
    return (chart,)


@app.cell
def _(alt, arr, df_orig, mat, mo, np, pd):
    x_sim = np.random.multivariate_normal(
        np.array(arr.matrix).reshape(-1), 
        np.array(mat.matrix), 
        2500
    )
    df_sim = pd.DataFrame({"x": x_sim[:, 0], "y": x_sim[:, 1]})

    chart_sim = (
        alt.Chart(df_sim).mark_point().encode(x="x", y="y") + 
        alt.Chart(df_orig).mark_point(color="gray").encode(x="x", y="y")
    )

    mo.vstack([
        mo.md("""
    ## `Matrix` demo

    ```python
    from wigglystuff import Matrix

    arr = Matrix(rows=1, cols=2, step=0.1)
    mat = Matrix(matrix=np.eye(2), mirror=True, step=0.1)
    ```

    This demo contains a representation of a two dimensional gaussian distribution. You can adapt the center by changing the first array that represents the mean and the variance can be updated by alterering the second one that represents the covariance matrix. Notice how the latter matrix has a triangular constraint."""),
        mo.hstack([arr, mat, chart_sim])
    ])
    return chart_sim, df_sim, x_sim


@app.cell
def _(Matrix, mo, np, pd):
    pca_mat = mo.ui.anywidget(Matrix(np.random.normal(0, 1, size=(3, 2)), step=0.1))
    rgb_mat = np.random.randint(0, 255, size=(1000, 3))
    color = ["#{0:02x}{1:02x}{2:02x}".format(r, g, b) for r,g,b in rgb_mat]

    rgb_df = pd.DataFrame({
        "r": rgb_mat[:, 0], "g": rgb_mat[:, 1], "b": rgb_mat[:, 2], 'color': color
    })
    return color, pca_mat, rgb_df, rgb_mat


@app.cell
def _(alt, color, mo, pca_mat, pd, rgb_mat):
    X_tfm = rgb_mat @ pca_mat.matrix
    df_pca = pd.DataFrame({"x": X_tfm[:, 0], "y": X_tfm[:, 1], "c": color})
    pca_chart = alt.Chart(df_pca).mark_point().encode(x="x", y="y", color=alt.Color('c:N', scale = None))

    mo.vstack([
        mo.md("""
    ### PCA demo with `Matrix` 

    Ever want to do your own PCA? Try to figure out a mapping from a 3d color map to a 2d representation with the transformation matrix below."""),
        mo.hstack([pca_mat, pca_chart])
    ])
    return X_tfm, df_pca, pca_chart


@app.cell
def _(c, coffees, mo, price, prob1, prob2, saying, shouting, times, total):
    mo.vstack([
        mo.md(f"""
        ## Tangle objects 

        Very much inspired by [tangle.js](), this library also offers some sliders/choice elements that can natively be combined in markdown. 

        ```python
        from wigglystuff import TangleSlider
        ```

        There are some examples below. 
        ### Apples example 

        Suppose that you have {coffees} and they each cost {price} then in total you would need to spend ${total:.2f}. 

        ### Amdhals law

        You cannot always get a speedup by throwing more compute at a problem. Let's compare two scenarios. 

        - You might have a parallel program that needs to sync up {prob1}.
        - Another parallel program needs to sync up {prob2}.

        The consequences of these choices are shown below. You might be suprised at the result, but you need to remember that if you throw more cores at the problem then you will also have more cores that will idle when the program needs to sync. 

        """),
        c,
        mo.md(f"""
        ### Also a choice widget 

        The slider widget can do numeric values for you, but sometimes you also want to make a choice between discrete choices. For that, you can use the `TangleChoice` widget. 

        ```python
        from wigglystuff import TangleChoice
        ```

        As a quick demo, let's repeat {saying} {times}. 

        {" ".join([saying.choice] * int(times.amount))}
        """
        ),
        mo.md(f"""
        ### Also a select widget 

        Like `TangleChoice` but as a drop-down

        ```python
        from wigglystuff import TangleSelect
        ```

        As a quick demo, let's repeat {shouting} {times}. 

        {" ".join([shouting.choice] * int(times.amount))}
        """
        )
    ])
    return


@app.cell
def _(color_picker, mo):
    mo.vstack(
        [
            mo.md(f"""
        ## Pick colors

        Pick colors using a standard browser color input.

        ```python
        from wigglystuff import ColorPicker
        ColorPicker(color="#444444")
        ```

        You can use a color picker with marimo's `Html` to affect how things are rendered. 
        """),
            mo.Html(f'<p style="color: {color_picker.color}">Change my color!</p>'),
            mo.hstack([
                color_picker,
                mo.md(f"You selected {color_picker.value['color']} which is {color_picker.rgb} in RGB values.")
            ]),
        ]
    )
    return


@app.cell
def _(edge_widget, mo):
    mo.vstack([
        mo.md(f"""
        ## Drawing Edges

        We even have a tool that allows you to connect nodes by drawing edges!

        ```python
        from wigglystuff import EdgeDraw
        EdgeDraw(["a", "b", "c", "d"])
        ```

        Try it yourself by drawing below. 
        """),
        edge_widget,
        mo.md(f"""
        As you draw more nodes, you will also update the `widget.links` property. 
        """), 
        edge_widget.links

    ])
    return


@app.cell
def _(mo):
    mo.md(r"""## Appendix with all supporting code""")
    return


@app.cell
def _(mo):
    from wigglystuff import EdgeDraw

    edge_widget = mo.ui.anywidget(EdgeDraw(["a", "b", "c", "d"]))
    return EdgeDraw, edge_widget


@app.cell
def _(coffees, price):
    # You need to define derivates in other cells. 
    total = coffees.amount * price.amount
    return (total,)


@app.cell
def _(alt, np, pd, prob1, prob2):
    cores = np.arange(1, 64 + 1)
    p1, p2 = prob1.amount/100, prob2.amount/100
    eff1 = 1/(p1 + (1-p1)/cores)
    eff2 = 1/(p2 + (1-p2)/cores)

    df_amdahl = pd.DataFrame({
        'cores': cores, 
        f'{prob1.amount:.2f}% sync rate': eff1, 
        f'{prob2.amount:.2f}% sync rate': eff2
    }).melt("cores")

    c = (
        alt.Chart(df_amdahl)
            .mark_line()
            .encode(
                x='cores', 
                y=alt.Y('value').title("effective cores"), 
                color="variable"
            )
            .properties(width=500, title="Comparison between cores and actual speedup.")
    )
    return c, cores, df_amdahl, eff1, eff2, p1, p2


@app.cell
def _(mo):
    from wigglystuff import TangleSlider, TangleChoice, TangleSelect

    coffees = mo.ui.anywidget(TangleSlider(amount=10, min_value=0, step=1, suffix=" coffees", digits=0))
    price = mo.ui.anywidget(TangleSlider(amount=3.50, min_value=0.01, max_value=10, step=0.01, prefix="$", digits=2))
    prob1 = mo.ui.anywidget(TangleSlider(min_value=0, max_value=20, step=0.1, suffix="% of the time", amount=5))
    prob2 = mo.ui.anywidget(TangleSlider(min_value=0, max_value=20, step=0.1, suffix="% of the time", amount=0))
    saying = mo.ui.anywidget(TangleChoice(["🙂", "🎉", "💥"]))
    shouting = mo.ui.anywidget(TangleSelect(["🥔", "🥕", "🍎"]))
    times = mo.ui.anywidget(TangleSlider(min_value=1, max_value=20, step=1, suffix=" times", amount=3))
    return (
        TangleChoice,
        TangleSelect,
        TangleSlider,
        coffees,
        price,
        prob1,
        prob2,
        saying,
        shouting,
        times,
    )


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import micropip
    import numpy as np
    import pandas as pd

    # await micropip.install("wigglystuff==0.1.1")
    return alt, micropip, mo, np, pd


@app.cell
def _(mo, np):
    from wigglystuff import Matrix

    mat = mo.ui.anywidget(Matrix(matrix=np.eye(2), mirror=True, step=0.1))
    arr = mo.ui.anywidget(Matrix(rows=1, cols=2, step=0.1))
    return Matrix, arr, mat


@app.cell
def _(Matrix, mo, np):
    x1 = mo.ui.anywidget(Matrix(matrix=np.eye(2), step=0.1))
    x2 = mo.ui.anywidget(Matrix(matrix=np.random.random((2, 2)), step=0.1))
    return x1, x2


@app.cell
def _(mo):
    from wigglystuff import Slider2D

    slider_2d = mo.ui.anywidget(Slider2D(width=300, height=300))
    return Slider2D, slider_2d


@app.cell
def _(np, pd, slider_2d):
    df = pd.DataFrame({
        "x": np.random.normal(slider_2d.x * 10, 1, 2000), 
        "y": np.random.normal(slider_2d.y * 10, 1, 2000)
    })
    return (df,)


@app.cell
def _(np, pd):
    df_base = pd.DataFrame({
        "x": np.random.normal(0, 1, 2000), 
        "y": np.random.normal(0, 1, 2000)
    })
    return (df_base,)


@app.cell
def _(np, pd):
    x_orig = np.random.multivariate_normal(np.array([0, 0]), np.array([[1, 0], [0, 1]]), 2500)
    df_orig = pd.DataFrame({"x": x_orig[:, 0], "y": x_orig[:, 1]})
    return df_orig, x_orig


@app.cell
def _(mo):
    from wigglystuff import ColorPicker
    color_picker = mo.ui.anywidget(ColorPicker(color="#444444"))
    return ColorPicker, color_picker


if __name__ == "__main__":
    app.run()
