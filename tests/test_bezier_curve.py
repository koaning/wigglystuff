import math

import pytest
import traitlets

from wigglystuff import BezierCurve


def test_defaults_create_cubic_curve_and_current_point():
    widget = BezierCurve()

    assert len(widget.points) == 4
    assert widget.t == 0.0
    assert widget.current_point() == (widget.points[0]["x"], widget.points[0]["y"])
    assert widget.x == widget.points[0]["x"]
    assert widget.y == widget.points[0]["y"]


def test_t_is_clamped_and_refreshes_current_point():
    widget = BezierCurve(points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}])

    widget.t = 2

    assert widget.t == 1.0
    assert widget.current_point() == (1.0, 1.0)
    assert widget.x == 1.0
    assert widget.y == 1.0


def test_points_are_validated_and_coerced():
    widget = BezierCurve(points=[{"x": 0, "y": 1}])

    assert widget.points == [{"x": 0.0, "y": 1.0}]

    with pytest.raises(traitlets.TraitError, match="x and y"):
        widget.points = [{"x": 0}]

    with pytest.raises(traitlets.TraitError, match="numeric"):
        widget.points = [{"x": "nope", "y": 0}]


def test_bounds_and_sizes_are_validated():
    with pytest.raises(traitlets.TraitError, match="min < max"):
        BezierCurve(x_bounds=(1, 1))

    with pytest.raises(traitlets.TraitError, match="positive"):
        BezierCurve(width=0)

    with pytest.raises(traitlets.TraitError, match="positive"):
        BezierCurve(interval_ms=0)

    with pytest.raises(traitlets.TraitError, match="positive"):
        BezierCurve(duration_ms=0)

    with pytest.raises(traitlets.TraitError, match="non-negative"):
        BezierCurve(sync_throttle_ms=-1)


def test_closed_is_virtual_and_does_not_mutate_points():
    points = [{"x": 0, "y": 0}, {"x": 1, "y": 1}]
    widget = BezierCurve(points=points, closed=True)

    assert widget.points == [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}]
    assert widget.sample(3) == [
        {"x": 0.0, "y": 0.0},
        {"x": 0.5, "y": 0.5},
        {"x": 0.0, "y": 0.0},
    ]


def test_sample_matches_quadratic_de_casteljau():
    widget = BezierCurve(
        points=[
            {"x": 0, "y": 0},
            {"x": 1, "y": 1},
            {"x": 2, "y": 0},
        ]
    )

    samples = widget.sample(3)

    assert samples[0] == {"x": 0.0, "y": 0.0}
    assert samples[1] == {"x": 1.0, "y": 0.5}
    assert samples[2] == {"x": 2.0, "y": 0.0}


def test_current_point_with_empty_points_returns_nan_pair():
    widget = BezierCurve(points=[])

    x, y = widget.current_point()

    assert math.isnan(x)
    assert math.isnan(y)
    assert widget.sample() == []


def test_sample_requires_positive_count():
    widget = BezierCurve()

    with pytest.raises(ValueError, match="positive"):
        widget.sample(0)
