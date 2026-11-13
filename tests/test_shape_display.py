import pytest

pytest.importorskip("numpy")

import pickle

import numpy as np

from wigglystuff import shape_display


@pytest.fixture
def matrix():
    return shape_display(np.zeros((128, 2)), labels=("n", None))


def test_labels_defaults_value_and_setter(matrix):
    assert matrix.labels == ("n", None)
    assert shape_display(np.zeros((4, 4))).labels == (None, None)
    assert type(matrix.value) is np.ndarray
    matrix.labels = ("rows", None)
    assert matrix.labels == ("rows", None)


def test_construction_validation():
    with pytest.raises(ValueError, match="2D and 3D"):
        shape_display(np.zeros(4))
    with pytest.raises(ValueError, match="one entry per array axis"):
        shape_display(np.zeros((4, 4)), labels=("n",))
    with pytest.raises(TypeError, match="strings or None"):
        shape_display(np.zeros((4, 4)), labels=("n", 2))
    with pytest.raises(ValueError, match="empty"):
        shape_display(np.zeros((4, 4)), labels=("n", ""))


def test_labels_follow_axes_that_keep_their_size(matrix):
    assert (matrix + 10).labels == ("n", None)
    # Axes whose size changed fall back to the live size, so the caption
    # never lies.
    assert matrix[:10].labels == (None, None)
    assert np.concatenate([matrix, matrix], axis=1).labels == ("n", None)
    assert matrix.reshape(2, 128).labels == (None, None)
    assert np.stack([matrix, matrix]).labels == (None, None, None)


def test_matmul_labels_take_rows_left_and_columns_right():
    X = shape_display(np.zeros((128, 2)), labels=("n", "d"))
    W = shape_display(np.zeros((2, 3)), labels=("d", "k"))
    assert (X.T @ X).labels == ("d", "d")
    assert (X @ X.T).labels == ("n", "n")
    assert (X @ W).labels == ("n", "k")
    # A plain right operand has no column label; batch axes come along.
    assert (X @ np.ones((2, 2))).labels == ("n", None)
    batch = shape_display(np.zeros((32, 128, 2)), labels=("b", "n", "d"))
    assert (batch @ W).labels == ("b", "n", "k")


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
    assert op(matrix).labels == (None, "n")


def test_reduced_results_fall_back_to_plain_display(matrix):
    assert type(matrix.sum(axis=1)._display_()) is np.ndarray
    assert type(matrix.mean()._display_()) is np.ndarray


def test_render(matrix):
    html = matrix._display_().text
    assert "ws-shape-display" in html
    assert "n by 2" in html  # aria label
    tensor = shape_display(np.zeros((32, 8, 3)), labels=("batch", "n", None))
    assert "ws-shape-display-plane-back" in tensor._display_().text


def test_names_render():
    tex = shape_display(np.zeros((4, 4)), name=r"$\mathbf{X}$")._display_().text
    assert "<marimo-tex" in tex  # rendered by marimo's built-in KaTeX
    assert r"Array \mathbf{X} with shape 4 by 4" in tex
    # Words stay upright; a lone letter reads as an italic variable.
    assert ">logits<" in shape_display(np.zeros((4, 4)), name="logits")._display_().text
    assert "<i>X</i>" in shape_display(np.zeros((4, 4)), name="X")._display_().text


def test_name_sticks_to_views_only():
    named = shape_display(np.zeros((4, 4)), name="X")
    assert named[:2].name == "X"
    assert (named + 1).name is None
    assert np.concatenate([named, named]).name is None
    assert not hasattr(named.value, "name")


def test_matmul_and_transpose_infer_names():
    X = shape_display(np.zeros((4, 2)), name=r"$\mathbf{X}$")
    W = shape_display(np.zeros((2, 3)), name="W")
    assert X.T.name == r"${\mathbf{X}}^{\mathbf{T}}$"
    assert (X @ W).name == r"${\mathbf{X}}{W}$"
    assert (X.T @ X).name == r"${{\mathbf{X}}^{\mathbf{T}}}{\mathbf{X}}$"
    # Multi-letter plain names become \text{...}; unnamed operands drop it.
    assert (shape_display(np.zeros((3, 4)), name="a_b") @ X).name == r"${\text{a\_b}}{\mathbf{X}}$"
    assert (X @ np.ones((2, 2))).name is None


def test_set_name_returns_renamed_view():
    named = shape_display(np.zeros((4, 2)), labels=("n", None), name="X")
    renamed = (named + 1).set_name("Y")
    assert renamed.name == "Y"
    assert renamed.labels == ("n", None)
    assert named.name == "X"
    assert named.set_name(None).name is None


def test_pickle_round_trip():
    named = shape_display(np.arange(8).reshape(4, 2), labels=("n", None), name="X")
    restored = pickle.loads(pickle.dumps(named))
    assert type(restored) is type(named)
    assert restored.labels == ("n", None)
    assert restored.name == "X"
    assert np.array_equal(restored, named)


def test_name_validation_and_setter():
    with pytest.raises(TypeError, match="string or None"):
        shape_display(np.zeros((4, 4)), name=42)
    assert shape_display(np.zeros((4, 4)), name="  ").name is None
    named = shape_display(np.zeros((4, 4)), name="X")
    named.name = "Y"
    assert named.name == "Y"
