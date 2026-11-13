import pytest

pytest.importorskip("numpy")

import numpy as np

from wigglystuff import array_display
from wigglystuff.array_display import _tex_to_html


@pytest.fixture
def matrix():
    return array_display(np.zeros((128, 2)), display_shape=("n", None))


def test_display_shape_defaults_value_and_setter(matrix):
    assert matrix.display_shape == ("n", None)
    assert array_display(np.zeros((4, 4))).display_shape == (None, None)
    assert type(matrix.value) is np.ndarray
    matrix.display_shape = ("rows", None)
    assert matrix.display_shape == ("rows", None)


def test_construction_validation():
    with pytest.raises(ValueError, match="2D and 3D"):
        array_display(np.zeros(4))
    with pytest.raises(ValueError, match="one entry per array axis"):
        array_display(np.zeros((4, 4)), display_shape=("n",))
    with pytest.raises(TypeError, match="strings or None"):
        array_display(np.zeros((4, 4)), display_shape=("n", 2))
    with pytest.raises(ValueError, match="empty"):
        array_display(np.zeros((4, 4)), display_shape=("n", ""))


def test_operations_keep_labels(matrix):
    assert (matrix + 10).display_shape == ("n", None)
    assert np.concatenate([matrix, matrix]).display_shape == ("n", None)
    assert matrix[:10].display_shape == ("n", None)
    assert matrix[[0, 5]].display_shape == ("n", None)
    # A new axis from np.stack gets default labels.
    assert np.stack([matrix, matrix]).display_shape == (None, None, None)


@pytest.mark.parametrize(
    "op",
    [
        lambda a: a.T,
        lambda a: a.transpose(1, 0),
        lambda a: np.transpose(a),
        lambda a: np.transpose(a, (1, 0)),
        lambda a: a.swapaxes(0, 1),
        lambda a: np.swapaxes(a, 0, 1),
        lambda a: np.rot90(a),
        lambda a: np.moveaxis(a, 0, 1),
    ],
)
def test_axis_permutations_relabel(matrix, op):
    assert op(matrix).display_shape == (None, "n")


def test_reduced_results_fall_back_to_plain_display(matrix):
    assert type(matrix.sum(axis=1)._display_()) is np.ndarray
    assert type(matrix.mean()._display_()) is np.ndarray


def test_render(matrix):
    html = matrix._display_().text
    assert "ws-array-display" in html
    assert "n by 2" in html  # aria label
    tensor = array_display(np.zeros((32, 8, 3)), display_shape=("batch", "n", None))
    assert "ws-array-display-plane-back" in tensor._display_().text


def test_names_render():
    named = array_display(np.zeros((4, 4)), name=r"$\mathbf{X}$")
    assert named.name == r"$\mathbf{X}$"
    assert "𝐗" in named._display_().text
    assert "Array 𝐗 with shape 4 by 4" in named._display_().text
    # Words stay upright; a lone letter reads as an italic variable.
    assert ">logits<" in array_display(np.zeros((4, 4)), name="logits")._display_().text
    assert "<i>X</i>" in array_display(np.zeros((4, 4)), name="X")._display_().text


@pytest.mark.parametrize(
    "tex, want",
    [
        (r"$\mathbf{X}$", "𝐗"),
        (r"$X_i$", "<i>X</i><sub><i>i</i></sub>"),
        (r"$W^{(1)}$", "<i>W</i><sup>(1)</sup>"),
        (r"$\hat{\theta}$", "<i>θ\u0302</i>"),
        (r"$\mathcal{L}$", "ℒ"),
        (r"$\mathbb{R}^{n \times d}$", "ℝ<sup><i>n</i>×<i>d</i></sup>"),
        (r"$\mathbf{A}_{batch}$", "𝐀<sub><i>b</i><i>a</i><i>t</i><i>c</i><i>h</i></sub>"),
        (r"$\Sigma$", "Σ"),
    ],
)
def test_tex_names(tex, want):
    assert _tex_to_html(tex) == want


def test_name_follows_the_data():
    named = array_display(np.zeros((4, 4)), name=r"$\mathbf{X}$")
    assert (named + 1).name == r"$\mathbf{X}$"
    assert named[:2].name == r"$\mathbf{X}$"
    assert named.T.name == r"$\mathbf{X}$"
    # Arrays rebuilt from several inputs are not that variable anymore.
    assert np.concatenate([named, named]).name is None
    assert not hasattr(named.value, "name")


def test_name_validation_and_setter():
    with pytest.raises(TypeError, match="string or None"):
        array_display(np.zeros((4, 4)), name=42)
    assert array_display(np.zeros((4, 4)), name="  ").name is None
    named = array_display(np.zeros((4, 4)), name="X")
    named.name = "Y"
    assert named.name == "Y"
