import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import AnnotationWidget

    widget = mo.ui.anywidget(AnnotationWidget(width=800))
    return mo, widget


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Annotation Widget Demo

    This widget provides a UI input surface for annotation workflows.
    Use the buttons, keyboard shortcuts (click the capture area first), or
    a gamepad controller to trigger actions. Add notes in the text field
    or use the mic button for speech-to-text.
    """)
    return


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget):
    action = widget.action or "---"
    note = widget.note or "---"
    ts = widget.action_timestamp
    listening = widget.listening

    mo.md(f"""
    **Last action:** `{action}` &nbsp;&nbsp;|&nbsp;&nbsp;
    **Timestamp:** `{ts}` &nbsp;&nbsp;|&nbsp;&nbsp;
    **Listening:** `{listening}`

    **Current note:** `{note}`
    """)
    return


if __name__ == "__main__":
    app.run()
