"""Tests for AltairWidget."""

import pytest


def test_import_from_package():
    from wigglystuff import AltairWidget


def test_create_with_dict_spec():
    from wigglystuff.altair_widget import AltairWidget

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"name": "source_0", "values": [{"x": 1, "y": 2}]},
        "mark": "point",
        "encoding": {
            "x": {"field": "x", "type": "quantitative"},
            "y": {"field": "y", "type": "quantitative"},
        },
    }
    widget = AltairWidget(spec)
    assert widget.spec == spec


def test_create_with_altair_chart():
    alt = pytest.importorskip("altair")
    pd = pytest.importorskip("pandas")
    from wigglystuff.altair_widget import AltairWidget

    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    chart = alt.Chart(df).mark_point().encode(x="x", y="y")
    widget = AltairWidget(chart)
    assert "mark" in widget.spec or "layer" in widget.spec


def test_chart_setter():
    alt = pytest.importorskip("altair")
    pd = pytest.importorskip("pandas")
    from wigglystuff.altair_widget import AltairWidget

    df1 = pd.DataFrame({"x": [1], "y": [1]})
    df2 = pd.DataFrame({"x": [2], "y": [2]})
    chart1 = alt.Chart(df1).mark_point().encode(x="x", y="y")
    chart2 = alt.Chart(df2).mark_point().encode(x="x", y="y")

    widget = AltairWidget(chart1)
    old_spec = widget.spec
    widget.chart = chart2
    assert widget.spec != old_spec


def test_chart_getter_raises():
    from wigglystuff.altair_widget import AltairWidget

    widget = AltairWidget()
    with pytest.raises(AttributeError):
        _ = widget.chart


def test_invalid_input_raises():
    from wigglystuff.altair_widget import AltairWidget

    with pytest.raises(TypeError):
        AltairWidget("not a chart")


def test_empty_widget():
    from wigglystuff.altair_widget import AltairWidget

    widget = AltairWidget()
    assert widget.spec == {}


def test_default_dimensions():
    from wigglystuff.altair_widget import AltairWidget

    widget = AltairWidget()
    assert widget.width == 600
    assert widget.height == 400


def test_custom_dimensions():
    from wigglystuff.altair_widget import AltairWidget

    widget = AltairWidget(width=800, height=500)
    assert widget.width == 800
    assert widget.height == 500
