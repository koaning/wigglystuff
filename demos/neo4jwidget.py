# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "neo4j>=5.0.0",
#     "wigglystuff==0.2.24",
# ]
# ///

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Neo4j Widget

    Interactive graph explorer for Neo4j databases.
    Requires a running Neo4j instance.

    Update the connection details below to match your setup.
    """)
    return


@app.cell
def _(mo):
    uri_input = mo.ui.text(value="neo4j+s://demo.neo4jlabs.com", label="URI")
    user_input = mo.ui.text(value="movies", label="User")
    pass_input = mo.ui.text(value="movies", label="Password", kind="password")
    db_input = mo.ui.text(value="movies", label="Database")
    mo.hstack([uri_input, user_input, pass_input, db_input])
    return db_input, pass_input, uri_input, user_input


@app.cell
def _(db_input, mo, pass_input, uri_input, user_input):
    from wigglystuff import Neo4jWidget

    widget = mo.ui.anywidget(
        Neo4jWidget(
            uri=uri_input.value,
            auth=(user_input.value, pass_input.value),
            database=db_input.value,
            height=400
        )
    )
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    mo.md(f"""
    **Selected nodes:** {widget.selected_nodes}
    """)
    return


@app.cell
def _(widget):
    widget.get_selected_node_data()
    return


@app.cell
def _(widget):
    widget.value
    return


if __name__ == "__main__":
    app.run()
