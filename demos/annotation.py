import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import AnnotationWidget

    return AnnotationWidget, mo


@app.cell
def _(mo):
    mo.md(r"""
    ## Annotation Widget Demo

    This widget provides a UI input surface for annotation workflows.
    Use the buttons, keyboard shortcuts (click the capture area first), or
    a gamepad controller to trigger actions. Add notes in the text field
    or use the mic button for speech-to-text.
    """)
    return


@app.cell(hide_code=True)
def _(AnnotationWidget, mo):
    widget = mo.ui.anywidget(AnnotationWidget(width=600, height=500))
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget):
    mo.md(f"""
    **Last action:** `{widget.action or "---"}` &nbsp;&nbsp;|&nbsp;&nbsp;
    **Timestamp:** `{widget.action_timestamp}` &nbsp;&nbsp;|&nbsp;&nbsp;
    **Listening:** `{widget.listening}`

    **Current note:** `{widget.note or "---"}`
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## Annotation Experience

    Below is a more realistic example: a list of text examples is presented
    one at a time. Use the widget to label each as **accept**, **fail**, or
    **defer**, and use **previous** to go back and correct a label.
    """)
    return


@app.cell
def _(mo):
    examples = [
        "The food was absolutely delicious and the service was top notch.",
        "Terrible experience. The waiter was rude and the steak was overcooked.",
        "It was okay, nothing special. Might come back if nothing else is open.",
        "Best pizza I've ever had! Will definitely return.",
        "The ambiance was nice but the food took forever to arrive.",
        "Completely bland pasta. Would not recommend.",
        "Friendly staff, generous portions, fair prices. A hidden gem!",
        "I found a hair in my soup. Disgusting.",
    ]
    get_index, set_index = mo.state(0)
    get_annotations, set_annotations = mo.state({})
    return examples, get_annotations, get_index, set_annotations, set_index


@app.cell
def _(AnnotationWidget, mo):
    annot_widget = mo.ui.anywidget(AnnotationWidget(width=800))
    return (annot_widget,)


@app.cell
def _(
    annot_widget,
    examples,
    get_annotations,
    get_index,
    set_annotations,
    set_index,
):
    action = annot_widget.action
    note = annot_widget.note
    _ = annot_widget.action_timestamp

    _i = get_index()
    _annots = get_annotations()

    if action in ("accept", "fail", "defer"):
        _annots[_i] = {"label": action, "note": note}
        set_annotations(_annots)
        if _i < len(examples) - 1:
            set_index(_i + 1)
    elif action == "previous":
        if _i > 0:
            set_index(_i - 1)
    return


@app.cell
def _(annot_widget, examples, get_annotations, get_index, mo):
    _i = get_index()
    _annots = get_annotations()
    total = len(examples)
    done = len(_annots)

    prev_label = _annots.get(_i, {}).get("label", "")
    label_badge = f" — previously labeled **{prev_label}**" if prev_label else ""

    mo.vstack([
        mo.md(
            f"**All {total} examples labeled!**"
            if done >= total
            else f"**Example {_i + 1} / {total}** ({done} labeled){label_badge}\n\n> {examples[_i]}", 
        ), 
        annot_widget
    ])
    return


@app.cell
def _(examples, get_annotations, mo):
    _annots = get_annotations()
    rows = [
        {
            "index": idx,
            "text": text[:60] + ("..." if len(text) > 60 else ""),
            "label": _annots.get(idx, {}).get("label", ""),
            "note": _annots.get(idx, {}).get("note", ""),
        }
        for idx, text in enumerate(examples)
    ]
    mo.md(
        "### Annotations so far\n\n"
        + mo.as_html(mo.ui.table(rows, selection=None)).text
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
