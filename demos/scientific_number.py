# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.24",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ScientificNumber

    A text field for numbers across the full magnitude spectrum. Type plain
    decimals (`0.0001`) or scientific notation (`1e-30`) straight in, and add
    an optional `scale` factor so Python reads back a value that's already
    rescaled for you.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The problem: entering numbers at the extremes

    You want to enter, say, a physical quantity on the order of 1e-20 and vary
    it on a fixed grid. With a stock `mo.ui.number` you'd either

    1. type the decimal number with a bunch of zeros and hope you counted
       right, or
    2. scale the value yourself and hope you never forgot to rescale it when you read
       it back.

    `ScientificNumber` removes both pains. You specify the number as a decimal
    or in scientific notation — no more entering 20 zeros — and you can change
    the scaling freely: the UI displays the raw value you typed, and when you
    access the value from Python it's already scaled for you.

    It can also display the scale and even show units.

    > You have to keep track of the scale that gets applied to the Python value and the displayed scale
    > yourself — they're independent because of the units: you could write a
    >scale label of `1e+3` with the unit meter, or just write kilometer.
    """)
    return


@app.cell
def _():
    import marimo as mo
    from wigglystuff import ScientificNumber

    distance = mo.ui.anywidget(
        ScientificNumber(
            label="$\\text{Distance}$",
            unit_label="$\\text{m}$",
            scale=1e11,
            scale_label="$\\times 10^{11}$",
            value=1.496e11,
            width=360,
        )
    )

    return ScientificNumber, distance, mo


@app.cell
def _(distance, mo):

    # mo.hstack([distance, values_panel], justify="center")
    code = mo.md("""
    ```python
    distance = mo.ui.anywidget(
        ScientificNumber(
            label="$\\text{Distance}$",
            unit_label="$\\text{m}$",
            scale=1e11,
            scale_label="$\\times 10^{11}$",
            value=1.496e11,
            width=360,
        )
    )
    ```
    """)

    explain = mo.md(
        "On the left you can see the code, on the right the resulting widget. Try entering a number like `12.3e-2` and see the value get updated (and scaled!) automatically."
    )

    mo.vstack(
        [
            explain,
            mo.hstack(
                [
                    code,
                    mo.vstack(
                        [distance, mo.md(f"{distance.scaled_value}")],
                        align="center",
                    ),
                ],
                align="center",
                justify="space-around",
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(distance, mo):
    mo.md(rf"""
    You can access several values:

    | Property | Value |
    |---|---|
    | `.value["value"]` (scaled) | `{distance.value["value"]}` |
    | `.scaled_value` (alias) | `{distance.scaled_value}` |
    | `.raw_value` (what you typed) | `{distance.raw_value}` |
    | `.scale` | `{distance.scale}` |
    | `.unit_label` | `{distance.unit_label}` |
    | `.label` | `{distance.label}` |
    | `.notation` | `{distance.notation}` |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step snapping

    `step` snaps what you type — the *raw* value — to multiples of `step`.
    Because `value = raw_value × scale`, the scaled value Python sees moves in
    multiples of `step × scale` (here `0.001 × 1000 = 1`, so the scaled mass
    stays on whole kilograms).

    This widget also shows another cool feature: You can not only enter numbers in scientific notation but also display them in scientific notation!
    """)
    return


@app.cell
def _(ScientificNumber, mo):
    mass = mo.ui.anywidget(
        ScientificNumber(
            label="$\\text{Mass}$",
            unit_label="$\\text{kg}$",
            scale=1e3,
            step=1e-3,
            value=2.002e4,
            width=360,
            notation="scientific"
        )
    )
    mass
    return (mass,)


@app.cell
def _(mass, mo):
    mo.md(str(mass.scaled_value))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Some Examples

    The examples below show some of the things you can do with this widget.
    """)
    return


@app.cell
def _(ScientificNumber, mo):
    t1 = mo.ui.anywidget(
        ScientificNumber(
            label="$\\text{Mass}$",
            unit_label="$\\text{kg}$",
            scale=1e3,
            value=2.5e3,
            width=320,
        )
    )

    t2 = mo.ui.anywidget(
        ScientificNumber(
            unit_label="$\\text{m}$",
            scale=1e3,
            scale_label="$\\times 10^{3}$",
            value=2e3,
            width=320,
        )
    )

    t3 = mo.ui.anywidget(
        ScientificNumber(
            unit_label="$\\text{s}$",
            scale=1e-9,
            scale_label="$\\cdot 10^{-9}$",
            value=2e-9,
            width=320,
        )
    )

    t4 = mo.ui.anywidget(
        ScientificNumber(
            unit_label="$\\text{Pa}$",
            scale=1e6,
            scale_label="1e+6",
            value=3e6,
            width=320,
        )
    )

    t5 = mo.ui.anywidget(
        ScientificNumber(
            label="Charge",
            unit_label="$\\text{C}$",
            value=2.34e-8,
            notation="scientific",
            width=320,
        )
    )

    t6 = mo.ui.anywidget(
        ScientificNumber(
            label="Amount",
            scale=1e3,
            min=0,
            max=5e6,
            value=3e6,
            width=320,
        )
    )

    t7 = mo.ui.anywidget(
        ScientificNumber(
            label="Items",
            value=42,
            width=320,
        )
    )

    t8 = mo.ui.anywidget(
        ScientificNumber(
            label="Count",
            value=42,
            width=160,
        )
    )

    feature_rows = [
        {"explanation": mo.md("**KaTeX label & unit** — `label` and `unit_label` accept `$...$` KaTeX."), "widget": t1},
        {"explanation": mo.md("**Scale with `\\times`** — `scale_label=\"$\\times 10^{3}$\"`."), "widget": t2},
        {"explanation": mo.md("**Scale with `\\cdot`** — `scale_label=\"$\\cdot 10^{-9}$\"`."), "widget": t3},
        {"explanation": mo.md("**Scale as a plain number** — `scale_label=\"1e+6\"`."), "widget": t4},
        {"explanation": mo.md("**Scientific notation display** — `notation=\"scientific\"` formats the value as `2.34e-8`."), "widget": t5},
        {"explanation": mo.md("**Bounds** — `min`/`max` clamp the **scaled** `value`; with `scale=1e3` the box clamps `0`–`5000` raw → `0`–`5e6` scaled."), "widget": t6},
        {"explanation": mo.md("**Default value** — `value=42` seeds the start; omit `value` and it starts at `0`."), "widget": t7},
        {"explanation": mo.md("**Compact** — `width=160`."), "widget": t8},
    ]
    feature_table = mo.ui.table(feature_rows, selection=None, column_widths={"explanation": 400, "widget": 400}, wrapped_columns=["explanation"])
    feature_table
    return


@app.cell
def _(ScientificNumber, mo):
    inline_widget = mo.ui.anywidget(
        ScientificNumber(
            unit_label="$\\text{kg}$",
            scale=1e3,
            step=1e-3,
            value=2.002e3,
            width=110,
        ).inline()
    )

    mo.vstack([
        mo.md("### Inline mode"),
        mo.md(f"The sample weighs {inline_widget} — well under a tonne. `.inline()` makes the widget sit at text height inside a `mo.md` paragraph."),
    ])
    return


if __name__ == "__main__":
    app.run()
