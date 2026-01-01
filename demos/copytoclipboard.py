import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import CopyToClipboard

    default_snippet = "pip install wigglystuff"
    widget = mo.ui.anywidget(CopyToClipboard(text_to_copy=default_snippet))
    editor = mo.ui.text_area(label="Text to copy", value=default_snippet)
    return editor, mo, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(editor):
    editor
    return


@app.cell
def _(editor, widget):
    widget.text_to_copy = editor.value
    return


@app.cell
def _(mo, widget):
    preview = widget.text_to_copy
    truncated = preview if len(preview) < 80 else preview[:77] + "..."

    mo.callout("Click the button to copy the payload below:")
    mo.md(f"```text\n{truncated}\n```")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
