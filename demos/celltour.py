# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "anywidget==0.9.21",
#     "marimo>=0.23",
#     "numpy==2.3.5",
#     "wigglystuff==0.5.9",
# ]
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def setup():
    import marimo as mo
    from wigglystuff import CellTour
    return CellTour, mo


@app.cell
def tour(CellTour, mo):
    # The tour widget lives at the top of the notebook so the "Start Tour"
    # button is reachable in both edit mode and app mode (`marimo run` /
    # molab). Steps target other cells by their `cell_name` — which is the
    # function name marimo uses for that cell.
    tour = mo.ui.anywidget(
        CellTour(
            steps=[
                {
                    "cell_name": "intro",
                    "title": "Welcome",
                    "description": "CellTour highlights marimo cells one at a time. This works in both edit mode and app mode (since marimo 0.23).",
                },
                {
                    "cell_name": "content",
                    "title": "Target any named cell",
                    "description": "Each step references a cell by `cell_name=` (its function name in marimo), which matches the `[data-cell-name]` attribute marimo renders on each cell.",
                },
                {
                    "cell_name": "summary",
                    "title": "That's it",
                    "description": "Use CellTour to build short product tours for marimo apps you share — onboarding, walkthroughs, or guided demos.",
                },
            ]
        )
    )
    tour
    return


@app.cell
def intro(mo):
    mo.md("""
    # CellTour demo

    A small guided tour over the cells below. Press **Start Tour** above
    to step through the highlights.
    """)
    return


@app.cell
def content(mo):
    mo.md("""
    ## The content cell

    This cell has visible output, so it shows up as a tour target in
    app mode. In `marimo run` / molab, only cells with output are
    rendered — pointing a tour step at an imports-only cell would
    leave nothing to highlight.
    """)
    return


@app.cell
def summary(mo):
    mo.md("""
    ## Wrap-up

    The tour finishes here. You can rerun it any time by pressing the
    **Start Tour** button at the top of the page.
    """)
    return


if __name__ == "__main__":
    app.run()
