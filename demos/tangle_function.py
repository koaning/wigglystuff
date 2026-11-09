# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.37",
#     "annotated-types",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from typing import Literal
    from wigglystuff import TangleFunction


    def train(
        lr: float = 0.01,
        epochs: int = 10,
        optimizer: Literal["adam", "sgd", "rmsprop"] = "adam",
        shuffle: bool = True,
        run_name: str = "run-1",
    ):
        """A stand-in training function whose call we want to configure."""
        return locals()


    tf = mo.ui.anywidget(
        TangleFunction(
            train,
            theme="light",
            params={"lr": {"min_value": 0.0, "max_value": 1.0, "step": 0.001}},
        )
    )
    return TangleFunction, mo, tf, train


@app.cell
def _(tf):
    tf
    return


@app.cell(hide_code=True)
def _(mo, tf):
    args = ", ".join(f"{k}={v!r}" for k, v in tf.value["values"].items())
    mo.md(f"""
    Drag the **numbers**, click the **choices** (`optimizer`, `shuffle`), and
    click the **string** to edit it. While you drag, `values` follows along and
    `committed_values` keeps the arguments from before the drag. The current call is:

    ```python
    train({args})
    ```
    """)
    return


@app.cell
def _(tf, train):
    # Splat the live arguments straight into the real function.
    train(**tf.value["values"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Choices from an `Enum`

    Any parameter typed with a `Literal`, an `Enum`, or `bool` becomes a
    click-to-cycle control. You can also force one with `params={"x": {"options": [...]}}`.
    """)
    return


@app.cell
def _(TangleFunction, mo):
    import enum


    class Size(enum.Enum):
        SMALL = "s"
        MEDIUM = "m"
        LARGE = "l"


    def make_shirt(size: Size = Size.MEDIUM, quantity: int = 1, gift_wrap: bool = False):
        return locals()


    shirt = mo.ui.anywidget(TangleFunction(make_shirt, theme="light"))
    shirt
    return (shirt,)


@app.cell(hide_code=True)
def _(mo, shirt):
    mo.md(f"""
    `values = {shirt.value['values']}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Bounds & step from `annotated_types`

    A number is an unbounded scrubber by default. To give it a range or a step,
    annotate the parameter with [`annotated_types`](https://pypi.org/project/annotated-types/)
    constraints (`Ge`, `Le`, `Gt`, `Lt`, `MultipleOf`). These are the same
    constraints pydantic uses, so `pydantic.Field(ge=..., le=...)` works too.
    """)
    return


@app.cell
def _(TangleFunction, mo):
    from typing import Annotated
    from annotated_types import Ge, Gt, Le, MultipleOf


    def generate(
        temperature: Annotated[float, Ge(0.0), Le(2.0), MultipleOf(0.05)] = 0.7,
        top_k: Annotated[int, Gt(0)] = 40,
        seed: int = 0,
    ):
        return locals()


    gen = mo.ui.anywidget(TangleFunction(generate, theme="light"))
    gen
    return (gen,)


@app.cell(hide_code=True)
def _(gen, mo):
    mo.md(f"""
    `values = {gen.value['values']}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Old and new values

    Next to `values`, a `TangleFunction` also stores `committed_values`. While
    you drag a number, `values` follows the pointer and `committed_values` keeps
    the arguments from before the drag. When you let go, the two match again.
    Drag a number below to compare the old result with the new one.
    """)
    return


@app.cell
def _(TangleFunction, mo):
    def compound(principal: float = 1000.0, rate: float = 0.05, years: int = 10):
        return principal * (1 + rate) ** years


    growth = mo.ui.anywidget(
        TangleFunction(
            compound,
            theme="light",
            params={
                "principal": {"min_value": 0, "step": 50},
                "rate": {"min_value": 0, "max_value": 0.2, "step": 0.005},
                "years": {"min_value": 1, "max_value": 50},
            },
        )
    )
    growth
    return compound, growth


@app.cell(hide_code=True)
def _(compound, growth, mo):
    def call(args):
        return "compound(" + ", ".join(f"{k}={v:g}" for k, v in args.items()) + ")"

    new, old = growth.value["values"], growth.value["committed_values"]
    mo.md(f"""
    | | call | result |
    | --- | --- | --- |
    | `values` | `{call(new)}` | {compound(**new):,.2f} |
    | `committed_values` | `{call(old)}` | {compound(**old):,.2f} |
    """)
    return


if __name__ == "__main__":
    app.run()
