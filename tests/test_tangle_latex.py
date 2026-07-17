"""Tests for the TangleLatex widget's Python API."""

import pytest

from wigglystuff.tangle_latex import TangleLatex


def parameter(value=1, **overrides):
    spec = {
        "value": value,
        "min_value": -5,
        "max_value": 5,
        "step": 0.1,
    }
    spec.update(overrides)
    return spec


def test_multiple_parameters_and_repeated_markers_initialize_values():
    widget = TangleLatex(
        latex=r"f(x) = \tangle{a}x^2 + \tangle{b}x + \tangle{a}",
        parameters={
            "a": parameter(2.5),
            "b": parameter(1, min_value=-10, max_value=10, step=0.5),
        },
    )

    assert widget.values == {"a": 2.5, "b": 1.0}
    assert widget.parameters["a"]["display"] == "number"
    assert widget.parameters["a"]["symbol"] == "a"


def test_defaults_are_normalized_without_mutating_input():
    parameters = {"a": {"value": 2}}
    widget = TangleLatex(latex=r"y = \tangle{a}x", parameters=parameters)

    assert parameters == {"a": {"value": 2}}
    assert widget.parameters["a"] == {
        "value": 2.0,
        "min_value": -100.0,
        "max_value": 100.0,
        "step": 1.0,
        "digits": 1,
        "display": "number",
        "symbol": "a",
        "label": "parameter a",
        "pixels_per_step": 7,
        "color": {"light": "#246bce", "dark": "#75a7ff"},
    }


def test_color_string_and_theme_mapping_are_supported():
    widget = TangleLatex(
        latex=r"\tangle{a} + \tangle{b}",
        parameters={
            "a": parameter(color="tomato"),
            "b": parameter(color={"light": "#111111", "dark": "#eeeeee"}),
        },
    )

    assert widget.parameters["a"]["color"] == {
        "light": "tomato",
        "dark": "tomato",
    }
    assert widget.parameters["b"]["color"] == {
        "light": "#111111",
        "dark": "#eeeeee",
    }


def test_symbolic_display_custom_symbol_and_widget_flags():
    widget = TangleLatex(
        latex=r"p = \tangle{alpha}",
        parameters={
            "alpha": parameter(
                0.5,
                display="symbol",
                symbol=r"\alpha",
                digits=2,
                label="learning rate",
                pixels_per_step=4,
            )
        },
        display_mode=False,
        editor="inline",
        reveal_all_on_drag=True,
        theme="dark",
    )

    assert widget.parameters["alpha"]["display"] == "symbol"
    assert widget.parameters["alpha"]["symbol"] == r"\alpha"
    assert widget.parameters["alpha"]["digits"] == 2
    assert widget.parameters["alpha"]["label"] == "learning rate"
    assert widget.parameters["alpha"]["pixels_per_step"] == 4
    assert widget.display_mode is False
    assert widget.editor == "inline"
    assert widget.reveal_all_on_drag is True
    assert widget.theme == "dark"


def test_theme_defaults_to_auto():
    widget = TangleLatex(
        latex=r"y = \tangle{a}x",
        parameters={"a": parameter()},
    )

    assert widget.theme == "auto"


def test_replacing_values_dict_is_synced_traitlet_update():
    widget = TangleLatex(
        latex=r"y = \tangle{a}x + \tangle{b}",
        parameters={"a": parameter(2), "b": parameter(1)},
    )
    changes = []
    widget.observe(lambda change: changes.append(change["new"]), names="values")

    widget.values = {**widget.values, "a": 3.5}

    assert widget.values == {"a": 3.5, "b": 1.0}
    assert changes == [{"a": 3.5, "b": 1.0}]


def test_missing_parameter_configuration_is_rejected():
    with pytest.raises(ValueError, match="missing configuration.*b"):
        TangleLatex(
            latex=r"y = \tangle{a}x + \tangle{b}",
            parameters={"a": parameter()},
        )


def test_unused_parameter_configuration_is_rejected():
    with pytest.raises(ValueError, match="not referenced.*b"):
        TangleLatex(
            latex=r"y = \tangle{a}x",
            parameters={"a": parameter(), "b": parameter()},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"value": "nope"}, "value must be a finite number"),
        ({"value": 8}, "value must be between"),
        ({"min_value": 5, "max_value": 5}, "min_value must be less"),
        ({"step": 0}, "step must be positive"),
        ({"digits": -1}, "digits must be a non-negative integer"),
        ({"pixels_per_step": 0}, "pixels_per_step must be a positive integer"),
        ({"display": "assignment"}, "display must be 'number' or 'symbol'"),
        ({"color": {"light": "red"}}, "color mapping must contain"),
    ],
)
def test_invalid_parameter_configuration_is_rejected(overrides, message):
    with pytest.raises(ValueError, match=message):
        TangleLatex(
            latex=r"y = \tangle{a}x",
            parameters={"a": parameter(**overrides)},
        )


def test_invalid_editor_is_rejected():
    with pytest.raises(ValueError, match="editor must be 'popover' or 'inline'"):
        TangleLatex(
            latex=r"y = \tangle{a}x",
            parameters={"a": parameter()},
            editor="dialog",
        )


def test_invalid_theme_is_rejected():
    with pytest.raises(ValueError, match="theme must be 'auto', 'light', or 'dark'"):
        TangleLatex(
            latex=r"y = \tangle{a}x",
            parameters={"a": parameter()},
            theme="sepia",
        )


def test_formula_requires_at_least_one_parameter_marker():
    with pytest.raises(ValueError, match=r"at least one \\tangle"):
        TangleLatex(latex=r"y = x + 1", parameters={})
