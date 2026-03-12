import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## TextHighlight

    A widget for displaying text with highlighted entity spans, like NER visualization. You can view, add, and remove entities interactively.
    """)
    return


@app.cell
def _():
    from wigglystuff import TextHighlight

    return (TextHighlight,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Read-Only Display

    Use `editable=False` to show entities without any editing UI. This is useful for displaying NER results.
    """)
    return


@app.cell
def _(TextHighlight, mo):
    readonly_widget = mo.ui.anywidget(TextHighlight(
        text="Barack Obama visited Washington D.C. and met with representatives from the United Nations.",
        labels=["PER", "LOC", "ORG"],
        entities=[
            {"text": "Barack Obama", "label": "PER", "start": 0, "end": 12},
            {"text": "Washington D.C.", "label": "LOC", "start": 21, "end": 36},
            {"text": "United Nations", "label": "ORG", "start": 73, "end": 87},
        ],
        editable=False,
    ))
    readonly_widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Interactive Editing

    With `editable=True` (the default), select a label in the toolbar, then highlight text to add entities. Click an entity to select it, then press Delete to remove it.
    """)
    return


@app.cell
def _(TextHighlight, mo):
    text = "Barack Obama visited Washington D.C. and met with representatives from the United Nations."

    widget = mo.ui.anywidget(TextHighlight(
        text=text,
        labels=["PER", "LOC", "ORG"],
        entities=[
            {"text": "Barack Obama", "label": "PER", "start": 0, "end": 12},
            {"text": "Washington D.C.", "label": "LOC", "start": 21, "end": 36},
            {"text": "United Nations", "label": "ORG", "start": 73, "end": 87},
        ],
    ))
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Accessing Entity Data

    The widget syncs entities back to Python, so you can use them programmatically.
    """)
    return


@app.cell
def _(widget):
    widget.value["entities"]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Character Selection Mode

    Switch from token-level to character-level selection for finer control.
    """)
    return


@app.cell
def _(TextHighlight, mo):
    char_widget = mo.ui.anywidget(TextHighlight(
        text="The WHO recommends vaccination.",
        labels=["ABBREV", "ACTION"],
        selection_mode="character",
    ))
    char_widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Overlapping Entities

    When `allow_overlap=True`, overlapping entities are shown with colored underlines.
    """)
    return


@app.cell
def _(TextHighlight, mo):
    overlap_widget = mo.ui.anywidget(TextHighlight(
        text="New York City is a great place to visit.",
        labels=["LOC", "REGION"],
        allow_overlap=True,
        entities=[
            {"text": "New York City", "label": "LOC", "start": 0, "end": 13},
            {"text": "New York", "label": "REGION", "start": 0, "end": 8},
        ],
    ))
    overlap_widget
    return


if __name__ == "__main__":
    app.run()
