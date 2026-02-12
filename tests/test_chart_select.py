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
