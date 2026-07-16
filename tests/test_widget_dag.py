from wigglystuff import WidgetDAG
from wigglystuff.widget_dag import layered_layout


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


def test_widget_dag_stores_nodes_edges_and_layout():
    widget = WidgetDAG(
        nodes={"image": "<img>", "conv": "<img>"},
        edges=[("image", "conv")],
    )

    assert widget.nodes == {"image": "<img>", "conv": "<img>"}
    assert widget.edges == [["image", "conv"]]
    assert widget.layout is layered_layout
