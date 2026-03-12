# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "polars",
#     "numpy==2.4.3",
#     "scikit-learn==1.8.0",
#     "wigglystuff",
#     "matplotlib==3.10.8",
#     "pandas==3.0.1",
#     "umap-learn==0.5.11",
# ]
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import polars as pl
    from sklearn.datasets import fetch_openml
    from sklearn.decomposition import PCA
    from umap import UMAP
    from wigglystuff import ParallelCoordinates
    import matplotlib.pyplot as plt

    return PCA, ParallelCoordinates, UMAP, fetch_openml, mo, np, pl, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Fashion MNIST — Parallel Coordinates

    This notebook loads the Fashion MNIST dataset, reduces the 784 pixel features
    down to a handful of PCA components, and visualizes them with an interactive
    parallel coordinates plot. Use the brushes on each axis to filter and explore
    how different clothing categories separate in PCA space.
    """)
    return


@app.cell
def _(fetch_openml, np):
    mnist = fetch_openml("Fashion-MNIST", version=1, as_frame=False, parser="auto")
    images = mnist.data.astype(np.float32)
    labels = mnist.target.astype(int)

    label_names = {
        0: "T-shirt/top",
        1: "Trouser",
        2: "Pullover",
        3: "Dress",
        4: "Coat",
        5: "Sandal",
        6: "Shirt",
        7: "Sneaker",
        8: "Bag",
        9: "Ankle boot",
    }
    return images, label_names, labels


@app.cell
def _(
    PCA,
    UMAP,
    checkbox,
    images,
    label_names,
    labels,
    n_components_slider,
    n_samples_slider,
    np,
    pl,
):
    rng = np.random.default_rng(42)
    idx = rng.choice(len(images), size=n_samples_slider.value, replace=False)

    if checkbox.value:
        pca = UMAP(n_components=n_components_slider.value)
    else:
        pca = PCA(n_components=n_components_slider.value)

    components = pca.fit_transform(images[idx])

    df = pl.DataFrame(
        {f"PC{i + 1}": components[:, i] for i in range(n_components_slider.value)}
    ).with_columns(pl.Series("label", [label_names[labels[i]] for i in idx]))
    return df, idx


@app.cell(hide_code=True)
def _(mo):
    n_samples_slider = mo.ui.slider(
        start=500, stop=5000, step=500, value=2000, label="Number of samples"
    )
    n_components_slider = mo.ui.slider(start=3, stop=15, step=1, value=8, label="Components")
    checkbox = mo.ui.checkbox(label="UMAP")
    [n_samples_slider, n_components_slider, checkbox]
    return checkbox, n_components_slider, n_samples_slider


@app.cell(hide_code=True)
def _(ParallelCoordinates, df, mo):
    widget = mo.ui.anywidget(ParallelCoordinates(df, height=500, color_by="label"))
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(idx, images, label_names, labels, np, plt, widget):
    filtered = widget.widget.filtered_indices
    sample_idx = np.array(filtered[:10]) if len(filtered) >= 10 else np.array(filtered)

    fig, axes = plt.subplots(1, len(sample_idx), figsize=(2 * len(sample_idx), 2))
    if len(sample_idx) == 1:
        axes = [axes]
    for _ax, _si in zip(axes, sample_idx):
        _ax.imshow(images[idx[_si]].reshape(28, 28), cmap="gray")
        _ax.set_title(label_names[labels[idx[_si]]], fontsize=9)
        _ax.axis("off")
    plt.tight_layout()
    fig
    return


if __name__ == "__main__":
    app.run()
