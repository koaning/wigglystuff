import pytest

from wigglystuff import WidgetDAG
from wigglystuff.widget_dag import (
    _format_float_html,
    _order_and_route,
    _reduce_edges,
    layered_layout,
)


def test_layered_layout_columns_follow_a_linear_chain():
    cols = layered_layout(
        {"a": 1, "b": 1, "c": 1},
        [("a", "b"), ("b", "c")],
    )

    assert cols == {"a": 0, "b": 1, "c": 2}


def test_layered_layout_pulls_a_node_right_to_sit_before_its_earliest_child():
    # Diamond: root -> {left, right} -> sink. `left` has a longest path of 1 but
    # is pulled right to column 1 (just before sink at 2), same as `right`.
    cols = layered_layout(
        {"root": 1, "left": 1, "right": 1, "sink": 1},
        [("root", "left"), ("root", "right"), ("left", "sink"), ("right", "sink")],
    )

    assert cols == {"root": 0, "left": 1, "right": 1, "sink": 2}


def test_reduce_edges_follows_a_linear_chain():
    # a (cell A) -> b (cell B) -> c (cell C); B is an ancestor of C, A of B and C.
    ancestors = {"A": set(), "B": {"A"}, "C": {"A", "B"}}
    name_to_cell = {"a": "A", "b": "B", "c": "C"}
    edges = _reduce_edges(["a", "b", "c"], name_to_cell, ancestors)

    assert edges == [["a", "b"], ["b", "c"]]


def test_reduce_edges_drops_transitive_shortcut():
    # a is an ancestor of both b and c, but a->c is redundant via b.
    ancestors = {"A": set(), "B": {"A"}, "C": {"A", "B"}}
    name_to_cell = {"a": "A", "b": "B", "c": "C"}
    edges = _reduce_edges(["a", "b", "c"], name_to_cell, ancestors)

    assert ["a", "c"] not in edges


def test_reduce_edges_gives_shared_cell_nodes_no_edge():
    # a and b are defined in the same cell -> neither is the other's ancestor.
    ancestors = {"A": set()}
    name_to_cell = {"a": "A", "b": "A"}
    edges = _reduce_edges(["a", "b"], name_to_cell, ancestors)

    assert edges == []


def test_dice_graph_routes_long_edge_without_adjacent_layer_crossings():
    order = [
        "e1",
        "e2",
        "slider",
        "grp1_energy_left",
        "grp2_energy_left",
        "p_win_first",
        "p_win",
        "p_win_second",
    ]
    edges = [
        ["e1", "grp1_energy_left"],
        ["e2", "grp1_energy_left"],
        ["slider", "grp2_energy_left"],
        ["slider", "p_win_first"],
        ["grp1_energy_left", "p_win_second"],
        ["grp2_energy_left", "p_win_second"],
        ["p_win_first", "p_win"],
        ["p_win_second", "p_win"],
    ]
    columns = layered_layout(dict.fromkeys(order), edges)

    layers, routes, dummies = _order_and_route(order, columns, edges)

    slider_route = next(
        route
        for route in routes
        if route[0] == "slider" and route[-1] == "p_win_first"
    )
    assert len(slider_route) == 3
    assert slider_route[1] in dummies

    positions = {
        node: (column, row)
        for column, layer in layers.items()
        for row, node in enumerate(layer)
    }
    segments = [
        (positions[src], positions[dst])
        for route in routes
        for src, dst in zip(route, route[1:])
    ]
    crossings = sum(
        1
        for index, ((left_col, left_row), (right_col, right_row)) in enumerate(segments)
        for (
            (other_left_col, other_left_row),
            (other_right_col, other_right_row),
        ) in segments[index + 1 :]
        if left_col == other_left_col
        and right_col == other_right_col
        and (left_row - other_left_row) * (right_row - other_right_row) < 0
    )
    assert crossings == 0


def test_float_nodes_use_compact_text_and_keep_exact_value_in_tooltip():
    assert _format_float_html(0.49500000000000016) == (
        '<span title="Exact value: 0.49500000000000016">0.495</span>'
    )
    assert _format_float_html(1 / 3) == (
        '<span title="Exact value: 0.3333333333333333">0.3333</span>'
    )
    assert _format_float_html(1.0) == '<span title="Exact value: 1.0">1</span>'
    assert _format_float_html(1) is None


def test_widget_dag_stores_nodes_edges_and_layout():
    widget = WidgetDAG(
        nodes={"image": "<img>", "conv": "<img>"},
        edges=[("image", "conv")],
    )

    assert widget.nodes == {"image": "<img>", "conv": "<img>"}
    assert widget.edges == [["image", "conv"]]
    assert widget.layout is layered_layout


def test_widget_dag_display_raises_outside_marimo():
    # Tests run outside a marimo kernel, so both display hooks should refuse.
    widget = WidgetDAG(nodes={"a": "<img>"}, edges=[])
    with pytest.raises(RuntimeError, match="marimo-only"):
        widget._display_()
    with pytest.raises(RuntimeError, match="marimo-only"):
        widget._repr_mimebundle_()
