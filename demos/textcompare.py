import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## TextCompare

    A side-by-side text comparison widget that highlights matching passages between two texts. Useful for plagiarism detection, finding shared passages, or comparing document versions.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import TextCompare

    text_a = """The quick brown fox jumps over the lazy dog.
    This is a unique sentence in text A.
    Both texts share this common passage here.
    Another unique line for the first text."""

    text_b = """A quick brown fox leaps over a lazy dog.
    This is different content in text B.
    Both texts share this common passage here.
    Some other unique content for text B."""

    widget = mo.ui.anywidget(TextCompare(text_a=text_a, text_b=text_b, min_match_words=3))
    widget
    return TextCompare, widget


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Hover over highlighted matches in one panel to see the corresponding match highlighted in the other panel. The widget automatically scrolls to show the matching passage.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Accessing Match Data

    The widget exposes the detected matches programmatically, making it useful for analysis.
    """)
    return


@app.cell
def _(widget):
    widget.matches
    return


@app.cell(hide_code=True)
def _(mo, widget):
    mo.md(f"""
    **Found {len(widget.matches)} matching passages**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Adjusting Sensitivity

    The `min_match_words` parameter controls how many consecutive words are needed to count as a match.
    """)
    return


@app.cell
def _(TextCompare, mo):
    # More sensitive - catches smaller matches
    sensitive = mo.ui.anywidget(TextCompare(
        text_a="one two three four five 1 2 3 4",
        text_b="zero one two three four six 2 3 4",
        min_match_words=3
    ))
    sensitive
    return (sensitive,)


@app.cell
def _(sensitive):
    sensitive.matches
    return


@app.cell(hide_code=True)
def _():
    return


if __name__ == "__main__":
    app.run()
