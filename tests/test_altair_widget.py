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


def test_layered_chart_spec_preserved():
    """Layered chart specs should preserve datasets and layer data refs.

    This validates the Python-side spec shape only. The JS-side fix
    (prepareSpec handling multiple datasets) must be verified in a browser
    via ``marimo edit demos/altairwidget.py``.
    """
    alt = pytest.importorskip("altair")
    pd = pytest.importorskip("pandas")
    from wigglystuff.altair_widget import AltairWidget

    df1 = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    df2 = pd.DataFrame({"x": [1, 2, 3], "y": [6, 5, 4]})

    chart = alt.layer(
        alt.Chart(df1).mark_point().encode(x="x:Q", y="y:Q"),
        alt.Chart(df2).mark_line().encode(x="x:Q", y="y:Q"),
    )
    widget = AltairWidget(chart)

    assert "layer" in widget.spec
    assert "datasets" in widget.spec
    assert len(widget.spec["layer"]) == 2
    assert len(widget.spec["datasets"]) == 2

    for layer_spec in widget.spec["layer"]:
        assert "data" in layer_spec
        assert "name" in layer_spec["data"]
        assert layer_spec["data"]["name"] in widget.spec["datasets"]


def test_hconcat_chart_spec_preserved():
    """Concatenated chart specs should pass through with datasets intact."""
    alt = pytest.importorskip("altair")
    pd = pytest.importorskip("pandas")
    from wigglystuff.altair_widget import AltairWidget

    df1 = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    df2 = pd.DataFrame({"a": [5, 6], "b": [7, 8]})

    chart = alt.hconcat(
        alt.Chart(df1).mark_point().encode(x="x:Q", y="y:Q"),
        alt.Chart(df2).mark_bar().encode(x="a:Q", y="b:Q"),
    )
    widget = AltairWidget(chart)

    assert "hconcat" in widget.spec
    assert "datasets" in widget.spec
    assert len(widget.spec["datasets"]) == 2


def test_single_chart_with_datasets():
    """A single Altair chart still produces a datasets dict; verify it passes through."""
    alt = pytest.importorskip("altair")
    pd = pytest.importorskip("pandas")
    from wigglystuff.altair_widget import AltairWidget

    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    chart = alt.Chart(df).mark_point().encode(x="x:Q", y="y:Q")
    widget = AltairWidget(chart)

    assert "datasets" in widget.spec
    assert len(widget.spec["datasets"]) == 1
    assert "data" in widget.spec
    assert widget.spec["data"]["name"] in widget.spec["datasets"]
