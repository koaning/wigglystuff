# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair==5.5.0",
#     "marimo",
#     "matplotlib==3.10.1",
#     "moboard==0.1.0",
#     "mohtml==0.1.7",
#     "numpy==2.2.5",
#     "polars==1.29.0",
# ]
# ///

import marimo

__generated_with = "0.17.8"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from wigglystuff import KeystrokeWidget
    return KeystrokeWidget, mo


@app.cell
def _(KeystrokeWidget, mo):
    widget = mo.ui.anywidget(KeystrokeWidget())
    widget
    return (widget,)


@app.cell
def _(widget):
    widget.value
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
