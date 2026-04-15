"""Tests for ChartSelect widget."""

import numpy as np
import pytest

plt = pytest.importorskip("matplotlib.pyplot")

from wigglystuff.chart_select import ChartSelect


def test_from_callback_allows_get_mask_during_initial_draw():
    x_data = np.array([1.0, 2.0, 3.0])
    y_data = np.array([1.0, 2.0, 3.0])

    def draw_fn(ax, widget):
        mask = widget.get_mask(x_data, y_data)
        ax.scatter(x_data[~mask], y_data[~mask], alpha=0.4)
        if mask.any():
            ax.scatter(x_data[mask], y_data[mask], alpha=0.8)

    widget = ChartSelect.from_callback(
        draw_fn=draw_fn,
        x_bounds=(0.0, 4.0),
        y_bounds=(0.0, 4.0),
    )

    assert widget.has_selection is False
    assert widget.selection == {}
    assert widget.get_mask(x_data, y_data).tolist() == [False, False, False]


def test_point_data_default_empty():
    fig, ax = plt.subplots()
    ax.scatter([1, 2], [3, 4])
    widget = ChartSelect(fig)
    plt.close(fig)
    assert widget.point_data == []


def test_point_data_accepts_dicts():
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [4, 5, 6])
    widget = ChartSelect(fig)
    plt.close(fig)

    points = [
        {"x": 1.0, "y": 4.0, "name": "sig_1", "category": "A"},
        {"x": 2.0, "y": 5.0, "name": "sig_2", "category": "B"},
        {"x": 3.0, "y": 6.0, "name": "sig_3", "category": "A"},
    ]
    widget.point_data = points
    assert len(widget.point_data) == 3
    assert widget.point_data[0]["name"] == "sig_1"
    assert widget.point_data[1]["category"] == "B"


def test_point_data_backward_compatible():
    """ChartSelect works without point_data (backward compatible)."""
    fig, ax = plt.subplots()
    ax.scatter([1, 2], [3, 4])
    widget = ChartSelect(fig, mode="lasso")
    plt.close(fig)

    # All existing functionality works without point_data
    assert widget.mode == "lasso"
    assert widget.has_selection is False
    assert widget.point_data == []
    mask = widget.get_mask([1, 2], [3, 4])
    assert mask.tolist() == [False, False]
