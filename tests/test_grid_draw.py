import pytest

from wigglystuff import GridDraw


def test_defaults_match_spec():
    widget = GridDraw()

    assert widget.rows == 8
    assert widget.cols == 8
    assert widget.line_width == 2
    assert widget.dot_radius == 6
    assert widget.theme is None
    assert widget.width == 440
    assert widget.height == 440
    assert widget.dots == []
    assert widget.lines == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rows": 0},
        {"cols": 0},
        {"dot_radius": 0},
        {"width": 0},
        {"height": 0},
        {"line_width": 0},
        {"line_width": []},
        {"line_width": [1, 0]},
        {"line_width": [1, "2"]},
        {"theme": "sepia"},
    ],
)
def test_constructor_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        GridDraw(**kwargs)


@pytest.mark.parametrize(
    "name,value",
    [
        ("rows", 0),
        ("cols", 0),
        ("dot_radius", 0),
        ("width", 0),
        ("height", 0),
        ("line_width", 0),
        ("line_width", []),
        ("theme", "sepia"),
    ],
)
def test_runtime_config_trait_validation(name, value):
    widget = GridDraw()

    with pytest.raises(ValueError):
        setattr(widget, name, value)


def test_line_width_accepts_positive_int_or_list():
    fixed = GridDraw(line_width=3)
    pickable = GridDraw(line_width=[1, 2, 4])

    assert fixed.line_width == 3
    assert pickable.line_width == [1, 2, 4]


def test_add_dot_is_idempotent_and_validates_bounds():
    widget = GridDraw(rows=2, cols=3)

    widget.add_dot(2, 3)
    widget.add_dot(2, 3)

    assert widget.dots == [[2, 3]]
    with pytest.raises(ValueError, match="outside the grid"):
        widget.add_dot(3, 0)
    with pytest.raises(ValueError, match="outside the grid"):
        widget.add_dot(0, 4)


def test_add_line_canonicalizes_and_is_idempotent():
    widget = GridDraw(rows=2, cols=3, line_width=[2, 4])

    widget.add_line((0, 1), (0, 0), width=4)
    widget.add_line((0, 0), (0, 1), width=2)

    assert widget.lines == [{"from": [0, 0], "to": [0, 1], "width": 4}]


def test_add_line_defaults_to_current_default_width():
    widget = GridDraw(line_width=[3, 6])

    widget.add_line((1, 1), (2, 1))

    assert widget.lines == [{"from": [1, 1], "to": [2, 1], "width": 3}]


@pytest.mark.parametrize(
    "a,b",
    [
        ((0, 0), (1, 1)),
        ((0, 0), (0, 2)),
        ((0, 0), (0, 0)),
        ((-1, 0), (0, 0)),
        ((0, 0), (9, 0)),
    ],
)
def test_add_line_rejects_invalid_segments(a, b):
    widget = GridDraw()

    with pytest.raises(ValueError):
        widget.add_line(a, b)


def test_clear_removes_both_layers():
    widget = GridDraw()
    widget.add_dot(1, 1)
    widget.add_line((0, 0), (0, 1))

    widget.clear()

    assert widget.dots == []
    assert widget.lines == []
