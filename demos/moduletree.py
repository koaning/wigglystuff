# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.2.21",
#     "torch>=2.0",
# ]
# ///

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md(
        """
        # ModuleTreeWidget

        An interactive tree viewer for PyTorch `nn.Module` architecture.
        It shows the full module hierarchy with parameter counts, shapes,
        trainable/frozen/buffer badges, and a density indicator.
        """
    )
    return (mo,)


@app.cell
def _():
    import torch.nn as nn
    from wigglystuff import ModuleTreeWidget

    return ModuleTreeWidget, nn


@app.cell
def _(ModuleTreeWidget, nn):
    model = nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Linear(256, 10),
    )

    widget = ModuleTreeWidget(model, initial_expand_depth=2)
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    mo.md(f"""
    **Total parameters:** {widget.tree.get('total_param_count', 0):,}

    **Trainable parameters:** {widget.tree.get('total_trainable_count', 0):,}
    """)
    return


if __name__ == "__main__":
    app.run()
