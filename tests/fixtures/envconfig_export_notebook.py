# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "anywidget==0.11.0",
#     "marimo>=0.23.3",
#     "wigglystuff==0.3.5",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import EnvConfig

    config = mo.ui.anywidget(EnvConfig(["WIGGLYSTUFF_EXPORT_SECRET"]))
    config
    return (config,)


@app.cell
def _(config):
    'WIGGLYSTUFF_EXPORT_SECRET' in config
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
