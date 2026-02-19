"""Tests for the ScatterWidget."""

import pytest
import traitlets

from wigglystuff import ScatterWidget


def test_default_construction():
    widget = ScatterWidget()
    assert widget.n_classes == 4
    assert widget.brushsize == 40
    assert widget.width == 800
    assert widget.height == 400
    assert widget.data == []


def test_custom_n_classes():
    widget = ScatterWidget(n_classes=2)
    assert widget.n_classes == 2


def test_invalid_n_classes_zero():
    with pytest.raises(ValueError, match="n_classes must be between 1 and 4"):
        ScatterWidget(n_classes=0)


def test_invalid_n_classes_five():
    with pytest.raises(ValueError, match="n_classes must be between 1 and 4"):
        ScatterWidget(n_classes=5)


def test_invalid_n_classes_assignment():
    widget = ScatterWidget(n_classes=2)
    with pytest.raises(traitlets.TraitError, match="n_classes must be between 1 and 4"):
        widget.n_classes = 5


def test_data_as_pandas():
    widget = ScatterWidget()
    widget.data = [
        {"x": 100, "y": 200, "color": "#1f77b4", "label": "a", "batch": 0},
        {"x": 300, "y": 100, "color": "#ff7f0e", "label": "b", "batch": 1},
    ]
    df = widget.data_as_pandas
    assert len(df) == 2
    assert list(df.columns) == ["x", "y", "color", "label", "batch"]


def test_data_as_polars():
    widget = ScatterWidget()
    widget.data = [
        {"x": 100, "y": 200, "color": "#1f77b4", "label": "a", "batch": 0},
    ]
    df = widget.data_as_polars
    assert len(df) == 1
    assert "x" in df.columns


def test_data_as_X_y_classification():
    widget = ScatterWidget(n_classes=2)
    widget.data = [
        {"x": 1, "y": 2, "color": "#1f77b4", "label": "a", "batch": 0},
        {"x": 3, "y": 4, "color": "#ff7f0e", "label": "b", "batch": 1},
    ]
    X, y = widget.data_as_X_y
    assert X.shape == (2, 2)
    assert len(y) == 2


def test_data_as_X_y_classification_single_color_still_classification():
    widget = ScatterWidget(n_classes=3)
    widget.data = [
        {"x": 1, "y": 2, "color": "#1f77b4", "label": "a", "batch": 0},
        {"x": 3, "y": 4, "color": "#1f77b4", "label": "a", "batch": 1},
    ]
    X, y = widget.data_as_X_y
    assert X.shape == (2, 2)
    assert y == ["#1f77b4", "#1f77b4"]


def test_data_as_X_y_regression():
    widget = ScatterWidget(n_classes=1)
    widget.data = [
        {"x": 1, "y": 2, "color": "#1f77b4", "label": "a", "batch": 0},
        {"x": 3, "y": 4, "color": "#1f77b4", "label": "a", "batch": 1},
    ]
    X, y = widget.data_as_X_y
    assert X.shape == (2, 1)
    assert y.shape == (2,)
