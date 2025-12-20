import numpy as np

from wigglystuff import EdgeDraw


def test_get_adjacency_matrix_is_symmetric_when_undirected():
    widget = EdgeDraw(names=["A", "B", "C", "D"])
    widget.links = [("A", "B"), ("C", "D")]

    matrix = widget.get_adjacency_matrix()

    expected = np.zeros((4, 4))
    expected[0, 1] = expected[1, 0] = 1
    expected[2, 3] = expected[3, 2] = 1

    np.testing.assert_array_equal(matrix, expected)


def test_get_adjacency_matrix_respects_direction():
    widget = EdgeDraw(names=["A", "B", "C"])
    widget.links = [("A", "B"), ("B", "C")]

    directed_matrix = widget.get_adjacency_matrix(directed=True)
    undirected_matrix = widget.get_adjacency_matrix(directed=False)

    assert directed_matrix[0, 1] == 1
    assert directed_matrix[1, 0] == 0
    assert directed_matrix[1, 2] == 1
    assert directed_matrix[2, 1] == 0
    assert undirected_matrix[1, 0] == 1
    assert undirected_matrix[2, 1] == 1


def test_get_neighbors_respects_directed_flag():
    widget = EdgeDraw(names=["A", "B", "C"])
    widget.links = [("A", "B"), ("C", "A")]

    assert widget.get_neighbors("A", directed=True) == ["B"]
    assert set(widget.get_neighbors("A", directed=False)) == {"B", "C"}


def test_has_cycle_handles_directed_and_undirected_cases():
    directed_widget = EdgeDraw(names=["A", "B", "C"])
    directed_widget.links = [("A", "B"), ("B", "C"), ("C", "B")]

    undirected_widget = EdgeDraw(names=["A", "B", "C"])
    undirected_widget.links = [("A", "B"), ("B", "C"), ("C", "A")]

    assert directed_widget.has_cycle(directed=True) is True
    assert undirected_widget.has_cycle(directed=False) is True


def test_init_accepts_links_and_directed():
    links = [("A", "B"), ("B", "C")]

    widget = EdgeDraw(names=["A", "B", "C"], links=links, directed=False)

    assert widget.links == [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}]
    assert widget.directed is False
    assert widget.get_adjacency_matrix()[0, 1] == 1
