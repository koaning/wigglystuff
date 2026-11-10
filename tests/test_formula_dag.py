"""Tests for the FormulaDAG widget's Python API."""

import pytest

from wigglystuff import FormulaDAG


def _chain():
    return FormulaDAG(
        {
            "vol": {"tex": r"\sigma_T = \tangle{s}\sqrt{\tangle{T}}", "fn": lambda s, T: s * T**0.5},
            "d1": {"tex": r"\note{why}{d_1} = 1/\use{vol}", "fn": lambda vol: 1 / vol},
            "x": {"tex": r"\use{d1}^2 + \tangle{k}", "fn": lambda d1, k: d1**2 + k},
        },
        parameters={"s": {"value": 0.5}, "T": {"value": 4}, "k": {"value": 1}},
        notes={"why": "the reason"},
    )


def test_edges_layers_and_reachability_follow_use_markers():
    widget = _chain()
    assert widget.edges == [("vol", "d1"), ("d1", "x")]
    assert widget.layers == [["vol"], ["d1"], ["x"]]
    assert widget.upstream("x") == {"vol", "d1"}
    assert widget.downstream("vol") == {"d1", "x"}
    with pytest.raises(ValueError, match="unknown formula"):
        widget.upstream("nope")


def test_givens_share_the_top_row_and_row_pushes_a_formula_down():
    def rows(widget):  # real formulas only; "!"-ids are lanes for long edges
        return [[n for n in layer if not n.startswith("!")] for layer in widget.layers]

    formulas = {
        "a": r"a = 1",
        "b": r"b = 2",
        "c": r"c = \use{a}",
        "d": r"d = \use{b} + \use{c}",
    }
    assert rows(FormulaDAG(formulas)) == [["a", "b"], ["c"], ["d"]]
    pushed = FormulaDAG({**formulas, "b": {"tex": r"b = 2", "row": 1}})
    assert sorted(rows(pushed)[1]) == ["b", "c"]
    # A minimum row drags everything that uses the formula down with it.
    deep = FormulaDAG({**formulas, "a": {"tex": r"a = 1", "row": 2}})
    assert rows(deep) == [["b"], [], ["a"], ["c"], ["d"]]
    for bad in (-1, True, "2"):
        with pytest.raises(ValueError, match="row must be"):
            FormulaDAG({"a": {"tex": "a = 1", "row": bad}})


def test_synced_formulas_split_the_output_and_list_their_inputs():
    by_name = {f["name"]: f for f in _chain().formulas}
    # The left-hand side is sent separately so the browser can swap in values.
    assert by_name["vol"]["lhs"] == r"\sigma_T"
    assert by_name["d1"]["symbol"] == "d_1"  # notes are stripped from the symbol
    assert by_name["d1"]["out_note"] == "why"  # ...but remembered for the swap
    assert by_name["x"]["lhs"] == ""  # no top-level "=": nothing to replace
    assert by_name["x"]["tex"] == r"\use{d1}^2 + \tangle{k}"
    # Parameters each fn depends on, followed through other formulas.
    assert by_name["vol"]["inputs"] == ["T", "s"]
    assert by_name["x"]["inputs"] == ["T", "k", "s"]


def test_outputs_follow_values_and_committed_outputs_wait_for_the_drag():
    widget = _chain()
    assert widget.outputs == pytest.approx({"vol": 1.0, "d1": 1.0, "x": 2.0})

    widget.dragging = True
    widget.values = {**widget.values, "T": 16}
    assert widget.outputs["vol"] == pytest.approx(2.0)
    assert widget.committed_outputs["vol"] == pytest.approx(1.0)

    widget.dragging = False
    widget.committed_values = dict(widget.values)
    assert widget.committed_outputs == pytest.approx(widget.outputs)


def test_failing_fn_reports_an_error_and_downstream_gets_none():
    widget = FormulaDAG(
        {
            "a": {"tex": r"a = 1/\tangle{k}", "fn": lambda k: 1 / k},
            "b": {"tex": r"b = \use{a}", "fn": lambda a: a + 1},
        },
        parameters={"k": {"value": 0}},
    )
    assert widget.outputs == {"a": None, "b": None}
    # The message wording differs across Python versions; the type does not.
    assert list(widget.output_errors) == ["a"]
    assert widget.output_errors["a"].startswith("ZeroDivisionError:")


def test_invalid_graphs_and_configuration_raise():
    cases = [
        ({}, "non-empty mapping"),
        ({"a": r"a = \use{a}"}, "cannot \\\\use itself"),
        ({"a": r"a = \use{zz}"}, "unknown formula"),
        ({"a": r"a = \use{b}", "b": r"b = \use{a}"}, "must not form a cycle"),
        ({"a": r"a = \tangle{k}"}, "missing configuration"),
        ({"a": {"tex": "a = 1", "fn": lambda nope: nope}}, "not a parameter or formula"),
        ({"a": {"tex": "a = 1", "fn": lambda b: b}, "b": {"tex": "b = 1", "fn": lambda a: a}}, "fns must not form a cycle"),
    ]
    for formulas, message in cases:
        with pytest.raises(ValueError, match=message):
            FormulaDAG(formulas)
    with pytest.raises(ValueError, match="more than one formula"):
        FormulaDAG({"a": r"a = \note{n}{x}", "b": r"b = \note{n}{y}"}, notes={"n": "twice"})
