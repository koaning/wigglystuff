# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.2.21",
#     "torch>=2.0",
#     "transformers>=4.0",
# ]
# ///

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # ModuleTreeWidget

    An interactive tree viewer for PyTorch `nn.Module` architecture.
    It shows the full module hierarchy with parameter counts, shapes,
    trainable/frozen/buffer badges.

    Pick an architecture below to explore its structure.
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import torch.nn as nn
    from wigglystuff import ModuleTreeWidget

    return ModuleTreeWidget, nn


@app.cell
def _(nn):
    class ResidualBlock(nn.Module):
        def __init__(self, channels):
            super().__init__()
            self.block = nn.Sequential(
                nn.Conv2d(channels, channels, 3, padding=1),
                nn.BatchNorm2d(channels),
                nn.ReLU(),
                nn.Conv2d(channels, channels, 3, padding=1),
                nn.BatchNorm2d(channels),
            )
            self.relu = nn.ReLU()

        def forward(self, x):
            return self.relu(self.block(x) + x)

    class TinyResNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.stem = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(),
            )
            self.layer1 = nn.Sequential(
                ResidualBlock(32),
                ResidualBlock(32),
            )
            self.layer2 = nn.Sequential(
                nn.Conv2d(32, 64, 3, stride=2, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(),
                ResidualBlock(64),
            )
            self.head = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(64, 10),
            )

        def forward(self, x):
            x = self.stem(x)
            x = self.layer1(x)
            x = self.layer2(x)
            return self.head(x)

    def build_mlp():
        return nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    def build_cnn():
        return nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    def build_transformer():
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=256, nhead=8, dim_feedforward=512, batch_first=True
        )
        return nn.TransformerEncoder(encoder_layer, num_layers=4)

    def build_bert():
        from transformers import BertModel, BertConfig

        config = BertConfig(
            hidden_size=768,
            num_hidden_layers=12,
            num_attention_heads=12,
            intermediate_size=3072,
        )
        return BertModel(config)

    def build_nested():
        return TinyResNet()

    architectures = {
        "MLP": build_mlp,
        "CNN": build_cnn,
        "Transformer encoder": build_transformer,
        "BERT (HuggingFace)": build_bert,
        "Custom nested (TinyResNet)": build_nested,
    }
    return architectures, build_cnn


@app.cell
def _(architectures, mo):
    dropdown = mo.ui.dropdown(
        options=list(architectures.keys()),
        value="Custom nested (TinyResNet)",
        label="Architecture",
    )
    dropdown
    return (dropdown,)


@app.cell
def _(ModuleTreeWidget, architectures, dropdown):
    model = architectures[dropdown.value]()
    widget = ModuleTreeWidget(model, initial_expand_depth=2)
    widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    If you really like this overview of the model, you can also use the `_display_` method to change the HTML representation in marimo.
    """)
    return


@app.cell
def _(ModuleTreeWidget, build_cnn):
    from torch.nn import Module

    Module._display_ = lambda d: ModuleTreeWidget(d)

    build_cnn()
    return


if __name__ == "__main__":
    app.run()
