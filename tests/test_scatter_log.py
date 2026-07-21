import pytest

from wigglystuff import ScatterLog


def test_append_single_and_named_series_with_bounded_history():
    log = ScatterLog(max_points=3, x_label="step", y_label="score")

    log.append(x=1, y=0.5)
    log.append(x=2, loss=0.4, accuracy=0.8)

    assert log.data == [
        {"x": 1, "y": 0.5, "color": None},
        {"x": 2, "y": 0.4, "color": "loss"},
        {"x": 2, "y": 0.8, "color": "accuracy"},
    ]
    assert log.spec["datasets"]["scatterlog"] == log.data
    assert log.spec["encoding"]["x"]["title"] == "step"
    assert log.spec["encoding"]["y"]["title"] == "score"
    assert log.spec["encoding"]["color"]["legend"] == {"orient": "bottom"}

    log.append(x=3, y=0.9)

    assert [point["x"] for point in log.data] == [2, 2, 3]


def test_data_is_a_copy_and_clear_resets_the_chart():
    log = ScatterLog()
    log.append(x=1, y=2, color="run")

    returned = log.data
    returned.clear()
    assert len(log.data) == 1

    log.clear()
    assert log.data == []
    assert log.spec == {}

    log.append(x=2, y=3)
    assert "color" not in log.spec["encoding"]


def test_max_points_must_be_positive():
    with pytest.raises(ValueError, match="max_points must be >= 1"):
        ScatterLog(max_points=0)
