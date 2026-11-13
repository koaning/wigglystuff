import numpy as np
import pandas as pd
import polars as pl
import pytest

from wigglystuff import PairPlot

X = np.array(
    [
        [0.0, 0.0, 5.0],
        [1.0, 1.0, 6.0],
        [2.0, 2.0, 7.0],
        [3.0, 3.0, 8.0],
        [np.nan, 1.5, 9.0],
    ]
)
BOX = {"type": "box", "x_index": 0, "y_index": 1, "x_min": 0.5, "x_max": 2.5, "y_min": 0.5, "y_max": 2.5}
LASSO = {"type": "lasso", "x_index": 0, "y_index": 1, "vertices": [[-0.5, -0.5], [1.5, -0.5], [1.5, 1.5], [-0.5, 1.5]]}


def test_numpy_input_defaults_and_payload():
    plot = PairPlot(X)
    assert plot.columns == ["x0", "x1", "x2"]
    assert plot.shape == (5, 3)
    assert plot.categories == []
    assert plot._matrix.dtype == np.float32 and plot._matrix.flags.c_contiguous
    assert plot._color_codes.dtype == np.int32 and plot._color_codes.shape == (5,)
    assert plot.mode == "box" and plot.layout == "full" and plot.filters == []


def test_dataframes_pick_numeric_columns_and_color_column():
    pdf = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0], "kind": ["y", "x", "y"], "note": list("pqr")})
    plot = PairPlot(pdf, color="kind")
    assert plot.columns == ["a", "b"]
    # Sorted category order, codes follow it, default palette per category.
    assert plot.categories == ["x", "y"]
    assert plot._color_codes.tolist() == [1, 0, 1]
    assert len(plot.palette) == 2

    plot.selection = {"type": "box", "x_index": 0, "y_index": 1, "x_min": 1.5, "x_max": 3.5, "y_min": 0, "y_max": 9}
    assert isinstance(plot.selected_data, pd.DataFrame)
    assert plot.selected_data["a"].tolist() == [2.0, 3.0]

    pldf = pl.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0], "kind": ["y", "x", "y"]})
    plot = PairPlot(pldf, columns=["b", "a"], color="kind", color_map={"x": "#123456"})
    assert plot.columns == ["b", "a"]
    assert plot.palette[0] == "#123456"
    plot.selection = {"type": "box", "x_index": 1, "y_index": 0, "x_min": 0, "x_max": 1.5, "y_min": 0, "y_max": 9}
    assert isinstance(plot.selected_data, pl.DataFrame)
    assert plot.selected_data["a"].to_list() == [1.0]


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        PairPlot(np.zeros(5))
    with pytest.raises(ValueError):
        PairPlot(np.zeros((5, 1)))
    with pytest.raises(ValueError):
        PairPlot(np.zeros((0, 3)))
    with pytest.raises(ValueError):
        PairPlot(X, columns=["only", "two"])
    with pytest.raises(ValueError):
        PairPlot(X, color=[1, 2])
    with pytest.raises(TypeError):
        PairPlot(X, color="not-a-column")
    with pytest.raises(ValueError):
        PairPlot(pd.DataFrame({"a": [1.0], "b": [2.0]}), color="missing")
    with pytest.raises(Exception):
        PairPlot(X, layout="upper")


def test_box_and_lasso_masks_skip_non_finite_rows():
    plot = PairPlot(X)
    plot.selection = BOX
    assert plot.get_indices().tolist() == [1, 2]
    assert plot.selected_count == 2
    assert plot.selected_data.shape == (2, 3)

    plot.selection = LASSO
    assert plot.get_indices().tolist() == [0, 1]

    plot.clear_selection()
    assert plot.selection == {} and plot.selected_count == 0
    assert not plot.get_mask().any()


def test_keep_exclude_reset_replay_filters():
    plot = PairPlot(X)
    plot.keep()  # no selection: nothing happens
    assert plot.filters == []

    plot.selection = BOX
    plot.keep()
    assert plot.filters == [{"action": "keep", "selection": BOX}]
    assert plot.selection == {}
    assert np.flatnonzero(plot.get_active_mask()).tolist() == [1, 2]

    # Selections only count rows that survive the filters.
    plot.selection = LASSO
    assert plot.get_indices().tolist() == [1]
    plot.exclude()
    assert np.flatnonzero(plot.get_active_mask()).tolist() == [2]
    assert plot.active_data.tolist() == [X[2].tolist()]

    plot.reset()
    assert plot.filters == [] and plot.get_active_mask().all()


def test_set_data_clears_state_and_bumps_version():
    plot = PairPlot(X)
    plot.selection = BOX
    plot.keep()
    version = plot.data_version
    plot.set_data(np.ones((3, 2)), columns=["p", "q"])
    assert plot.columns == ["p", "q"]
    assert plot.filters == [] and plot.selection == {}
    assert plot.data_version == version + 1
