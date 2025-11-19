import numpy as np

from wigglystuff import EdgeDraw


def test_get_adjacency_matrix_is_symmetric_when_undirected():
    widget = EdgeDraw(names=["A", "B", "C", "D"])
    widget.links = [
        {"source": "A", "target": "B"},
        {"source": "C", "target": "D"},
    ]

    matrix = widget.get_adjacency_matrix()

    expected = np.zeros((4, 4))
    expected[0, 1] = expected[1, 0] = 1
    expected[2, 3] = expected[3, 2] = 1

    np.testing.assert_array_equal(matrix, expected)


def test_get_adjacency_matrix_respects_direction():
    widget = EdgeDraw(names=["A", "B", "C"])
    widget.links = [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "C"},
    ]

    matrix = widget.get_adjacency_matrix(directed=True)

    assert matrix[0, 1] == 1
    assert matrix[1, 0] == 0
    assert matrix[1, 2] == 1
    assert matrix[2, 1] == 0


def test_get_neighbors_respects_directed_flag():
    widget = EdgeDraw(names=["A", "B", "C"])
    widget.links = [
        {"source": "A", "target": "B"},
        {"source": "C", "target": "A"},
    ]

    assert widget.get_neighbors("A", directed=True) == ["B"]
    assert set(widget.get_neighbors("A", directed=False)) == {"B", "C"}


def test_has_cycle_handles_directed_and_undirected_cases():
    directed_widget = EdgeDraw(names=["A", "B", "C"])
    directed_widget.links = [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "C"},
        {"source": "C", "target": "B"},
    ]

    undirected_widget = EdgeDraw(names=["A", "B", "C"])
    undirected_widget.links = [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "C"},
        {"source": "C", "target": "A"},
    ]

    assert directed_widget.has_cycle(directed=True) is True
    assert undirected_widget.has_cycle(directed=False) is True
