# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "anywidget==0.9.21",
#     "marimo",
# ]
# ///

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    import marimo as mo
    from wigglystuff import EnvConfig
    return EnvConfig, mo, os


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `EnvConfig` Widget

    The whole point of this widget is to make it easy to either load required environment variables or to set them from the notebook for tutorials. The widget will automatically try to load any environment variables, but you can also still set them manually and also add a validator.

    This way, the user can confirm that all the keys are correct before moving on to the rest of the tutorial. In our experience, this saves a whole lot of time wasted and makes for a nicer developer experience.
    """)
    return


@app.cell
def _(EnvConfig, mo, os):
    # Example with a validator callback
    def check_key(key):
        if len(key) < 5:
            raise ValueError("Key must be at least 5 characters")


    os.environ["VALIDATED_KEY"] = "hi"

    config_validated = mo.ui.anywidget(
        EnvConfig(
            {
                "VALIDATED_KEY": check_key,
                "MY_API_KEY": check_key,
                "SIMPLE_KEY": None,  # just existence check
            }
        )
    )
    return (config_validated,)


@app.cell
def _(config_validated):
    config_validated
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can fetch values from this widget directly.
    """)
    return


@app.cell
def _(config_validated):
    config_validated["MY_API_KEY"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can also check if all the inputs are valid. This is useful if you want to prevent other cells from running.
    """)
    return


@app.cell
def _(config_validated):
    config_validated.all_valid
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    If you want to raise an error when the inputs are invalid, you can use `require_valid()`.
    """)
    return


@app.cell
def _(config_validated):
    config_validated.require_valid()
    return


@app.cell(hide_code=True)
def _():
    return


if __name__ == "__main__":
    app.run()
