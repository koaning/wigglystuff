import numpy as np
import pytest

from wigglystuff import GraphWidget


def test_scalar_nodes_become_named_nodes_with_matching_ids():
    widget = GraphWidget(nodes=["Alpha", 7])

    assert widget.nodes == [
        {"name": "Alpha", "id": "Alpha"},
        {"name": "7", "id": "7"},
    ]


def test_bounded_layout_defaults_to_true_and_can_be_disabled():
    assert GraphWidget(nodes=["Alpha"]).bounded is True

    widget = GraphWidget(nodes=["Alpha"], bounded=False)

    assert widget.bounded is False


def test_unique_name_becomes_id_when_id_is_missing():
    widget = GraphWidget(nodes=[{"name": "Beta", "size": 18}])

    assert widget.nodes == [{"name": "Beta", "size": 18, "id": "Beta"}]


def test_duplicate_names_receive_generated_ids():
    widget = GraphWidget(nodes=["same", {"name": "same"}, {}])

    assert widget.nodes == [
        {"name": "same", "id": "node-0"},
        {"name": "same", "id": "node-1"},
        {"id": "node-2"},
    ]


def test_edges_resolve_endpoints_by_id_name_and_index():
    widget = GraphWidget(
        nodes=[
            "Alpha",
            {"name": "Beta"},
            {"id": "gamma", "name": "Gamma"},
        ],
        edges=[
            ("Alpha", "Beta"),
            {"source": "Beta", "target": "gamma", "name": "depends on"},
            (0, 2),
        ],
    )

    assert widget.edges == [
        {"source": "Alpha", "target": "Beta", "id": "edge-0"},
        {
            "source": "Beta",
            "target": "gamma",
            "name": "depends on",
            "id": "edge-1",
        },
        {"source": "Alpha", "target": "gamma", "id": "edge-2"},
    ]


def test_integer_endpoint_prefers_matching_id_before_index():
    widget = GraphWidget(nodes=[0, 1, 2], edges=[(2, 0)])

    assert widget.edges == [{"source": "2", "target": "0", "id": "edge-0"}]


def test_invalid_edge_endpoint_raises():
    with pytest.raises(ValueError, match="Unknown graph node endpoint"):
        GraphWidget(nodes=["A"], edges=[("A", "B")])


def test_add_and_remove_helpers_reassign_traitlets():
    widget = GraphWidget(nodes=["A"])

    node_id = widget.add_node("B", color="#ff0000")
    edge_id = widget.add_edge("A", "B", name="to B", width=3)

    assert node_id == "B"
    assert edge_id == "edge-0"
    assert widget.nodes[-1]["color"] == "#ff0000"
    assert widget.edges == [
        {"source": "A", "target": "B", "name": "to B", "width": 3, "id": "edge-0"}
    ]

    widget.remove_node("B")

    assert [node["id"] for node in widget.nodes] == ["A"]
    assert widget.edges == []


def test_attach_node_adds_node_and_edge_together():
    widget = GraphWidget(nodes=["A"])

    node_id, edge_id = widget.attach_node(
        "A",
        "B",
        color="#2563eb",
        edge_name="+6",
        edge_color="#0f766e",
    )

    assert node_id == "B"
    assert edge_id == "edge-0"
    assert widget.nodes == [
        {"name": "A", "id": "A"},
        {"name": "B", "color": "#2563eb", "id": "B"},
    ]
    assert widget.edges == [
        {
            "source": "A",
            "target": "B",
            "name": "+6",
            "color": "#0f766e",
            "id": "edge-0",
        }
    ]


def test_attach_node_can_attach_existing_node():
    widget = GraphWidget(nodes=["A", "B"])

    node_id, edge_id = widget.attach_node("A", "B", edge_name="+6")

    assert node_id == "B"
    assert edge_id == "edge-0"
    assert widget.nodes == [{"name": "A", "id": "A"}, {"name": "B", "id": "B"}]
    assert widget.edges == [
        {"source": "A", "target": "B", "name": "+6", "id": "edge-0"}
    ]


def test_attach_node_can_attach_existing_node_by_id_and_update_attrs():
    widget = GraphWidget(nodes=["A", {"id": "node-b", "name": "B"}])

    node_id, edge_id = widget.attach_node(
        "A", id="node-b", name="Better B", color="#2563eb"
    )

    assert node_id == "node-b"
    assert edge_id == "edge-0"
    assert widget.nodes[-1] == {
        "id": "node-b",
        "name": "Better B",
        "color": "#2563eb",
    }


def test_detach_node_removes_incident_edges_but_keeps_node_by_default():
    widget = GraphWidget(nodes=["A", "B", "C"], edges=[("A", "B"), ("B", "C")])
    widget.selected_nodes = ["B"]
    widget.selected_edges = ["edge-0", "edge-1"]

    widget.detach_node("B")

    assert widget.nodes == [
        {"name": "A", "id": "A"},
        {"name": "B", "id": "B"},
        {"name": "C", "id": "C"},
    ]
    assert widget.edges == []
    assert widget.selected_nodes == ["B"]
    assert widget.selected_edges == []


def test_detach_node_can_delete_node_too():
    widget = GraphWidget(nodes=["A", "B", "C"], edges=[("A", "B"), ("B", "C")])
    widget.selected_nodes = ["B"]
    widget.selected_edges = ["edge-0", "edge-1"]

    widget.detach_node("B", delete=True)

    assert widget.nodes == [{"name": "A", "id": "A"}, {"name": "C", "id": "C"}]
    assert widget.edges == []
    assert widget.selected_nodes == []
    assert widget.selected_edges == []


def test_remove_edge_by_id_or_index():
    widget = GraphWidget(nodes=["A", "B", "C"], edges=[("A", "B"), ("B", "C")])

    widget.remove_edge(0)
    assert [edge["id"] for edge in widget.edges] == ["edge-1"]

    widget.remove_edge("edge-1")
    assert widget.edges == []


def test_selection_helpers_return_data_and_clear_selection():
    widget = GraphWidget(nodes=["A", "B"], edges=[("A", "B")])
    widget.selected_nodes = ["A"]
    widget.selected_edges = ["edge-0"]

    assert widget.get_selected_node_data() == [{"name": "A", "id": "A"}]
    assert widget.get_selected_edge_data() == [
        {"source": "A", "target": "B", "id": "edge-0"}
    ]

    widget.clear_selection()

    assert widget.selected_nodes == []
    assert widget.selected_edges == []


def test_adjacency_matrix_respects_directed_flag():
    widget = GraphWidget(nodes=["A", "B"], edges=[("A", "B")])

    directed = widget.get_adjacency_matrix()
    undirected = widget.get_adjacency_matrix(directed=False)

    np.testing.assert_array_equal(directed, np.array([[0, 1], [0, 0]]))
    np.testing.assert_array_equal(undirected, np.array([[0, 1], [1, 0]]))
