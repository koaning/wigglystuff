# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.7",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import CircularSlider, CircularRangeSlider

    dial = mo.ui.anywidget(
        CircularSlider(start=0, stop=100, step=1, value=42, size=120, color="tomato", label="red")
    )
    span = mo.ui.anywidget(
        CircularRangeSlider(start=0, stop=10000, step=1, value=(0, 1800), size=120, label="blue")
    )
    return dial, mo, span


@app.cell
def _(dial, mo, span):
    mo.hstack([dial, span], justify="center", gap=2)
    return


@app.cell(hide_code=True)
def _(dial, mo, span):
    mo.md(f"""
    **Single value:** `{dial.value['value']:.1f}`

    **Range:** `({span.value['value'][0]:.1f}, {span.value['value'][1]:.1f})`
    """)
    return


if __name__ == "__main__":
    app.run()
