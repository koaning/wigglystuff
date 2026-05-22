import pytest
import traitlets

from wigglystuff import CurveEditor


def test_defaults_create_chart_space_curve():
    widget = CurveEditor()

    assert len(widget.points) >= 2
    assert widget.curve == "natural"
    assert widget.t == 0.0
    assert widget.x == widget.points[0]["x"]
    assert widget.y == widget.points[0]["y"]
    assert widget.tension == 0.0
    assert widget.alpha == 0.5
    assert widget.closed is False
    assert widget.playing is False
    assert widget.loop is False
    assert widget.selected_index == -1


def test_points_are_coerced_and_sorted_by_x():
    widget = CurveEditor(
        points=[
            {"x": 2, "y": "20"},
            {"x": 1, "y": 10},
            {"x": 1, "y": 11},
        ]
    )

    assert widget.points == [
        {"x": 1.0, "y": 10.0},
        {"x": 1.0, "y": 11.0},
        {"x": 2.0, "y": 20.0},
    ]


def test_closed_points_preserve_drawing_order():
    widget = CurveEditor(
        closed=True,
        points=[
            {"x": 1, "y": "10"},
            {"x": 0, "y": 0},
            {"x": 0.5, "y": 5},
        ],
    )

    assert widget.points == [
        {"x": 1.0, "y": 10.0},
        {"x": 0.0, "y": 0.0},
        {"x": 0.5, "y": 5.0},
    ]

    widget.points = [
        {"x": 0.75, "y": 7.5},
        {"x": 0.25, "y": 2.5},
        {"x": 1.0, "y": 10.0},
    ]

    assert widget.points == [
        {"x": 0.75, "y": 7.5},
        {"x": 0.25, "y": 2.5},
        {"x": 1.0, "y": 10.0},
    ]


def test_opening_closed_curve_sorts_points_by_x_and_keeps_selection():
    widget = CurveEditor(
        closed=True,
        selected_index=1,
        points=[
            {"x": 1, "y": 10},
            {"x": 0, "y": 0},
            {"x": 0.5, "y": 5},
        ],
    )

    widget.closed = False

    assert widget.points == [
        {"x": 0.0, "y": 0.0},
        {"x": 0.5, "y": 5.0},
        {"x": 1.0, "y": 10.0},
    ]
    assert widget.selected_index == 0


def test_points_are_validated():
    with pytest.raises(traitlets.TraitError, match="at least two"):
        CurveEditor(points=[{"x": 0, "y": 0}])

    widget = CurveEditor()

    with pytest.raises(traitlets.TraitError, match="x and y"):
        widget.points = [{"x": 0}, {"x": 1, "y": 1}]

    with pytest.raises(traitlets.TraitError, match="numeric"):
        widget.points = [{"x": "nope", "y": 0}, {"x": 1, "y": 1}]


def test_curve_name_is_validated():
    with pytest.raises(traitlets.TraitError, match="curve must be one of"):
        CurveEditor(curve="bundle")

    widget = CurveEditor(curve="step_before")

    assert widget.curve == "step_before"


def test_bounds_sizes_and_selection_are_validated():
    with pytest.raises(traitlets.TraitError, match="min < max"):
        CurveEditor(x_bounds=(1, 1))

    with pytest.raises(traitlets.TraitError, match="positive"):
        CurveEditor(width=0)

    with pytest.raises(traitlets.TraitError, match="positive"):
        CurveEditor(interval_ms=0)

    with pytest.raises(traitlets.TraitError, match="positive"):
        CurveEditor(duration_ms=0)

    with pytest.raises(traitlets.TraitError, match="non-negative"):
        CurveEditor(sync_throttle_ms=-1)

    with pytest.raises(traitlets.TraitError, match="-1 or non-negative"):
        CurveEditor(selected_index=-2)

    with pytest.raises(traitlets.TraitError, match="outside"):
        CurveEditor(selected_index=100)


def test_curve_parameters_are_clamped():
    widget = CurveEditor(tension=2, alpha=-1)

    assert widget.tension == 1.0
    assert widget.alpha == 0.0

    widget.tension = -5
    widget.alpha = 5

    assert widget.tension == 0.0
    assert widget.alpha == 1.0


def test_t_is_clamped_and_refreshes_current_point():
    widget = CurveEditor(points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}])

    widget.t = 2

    assert widget.t == 1.0
    assert widget.current_point() == (1.0, 1.0)
    assert widget.x == 1.0
    assert widget.y == 1.0


def test_closed_loop_is_virtual_and_does_not_mutate_points():
    widget = CurveEditor(
        points=[{"x": 0, "y": 0}, {"x": 1, "y": 1}],
        closed=True,
        t=1.0,
    )

    assert widget.points == [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}]
    assert widget.current_point() == (0.0, 0.0)
