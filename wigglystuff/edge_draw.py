from pathlib import Path
from typing import List

import anywidget
import numpy as np
import traitlets


class EdgeDraw(anywidget.AnyWidget):
    """Widget for drawing edges between named nodes."""

    _esm = Path(__file__).parent / "static" / "edgedraw.js"
    _css = Path(__file__).parent / "static" / "edgedraw.css"
    names = traitlets.List([]).tag(sync=True)
    links = traitlets.List([]).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)

    def __init__(self, names: List[str], height: int = 400, width: int = 600) -> None:
        """Create an EdgeDraw widget.

        Args:
            names: Ordered list of node labels.
            height: Canvas height in pixels.
            width: Canvas width in pixels.
        """
        super().__init__(names=names, height=height, width=width)

    def get_adjacency_matrix(self, directed: bool = False) -> np.ndarray:
        """Create an adjacency matrix from links and node names."""
        num_nodes = len(self.names)
        matrix = np.zeros((num_nodes, num_nodes))
        for nodes in self.links:
            src = self.names.index(nodes["source"])
            dst = self.names.index(nodes["target"])
            matrix[src][dst] = 1
            if not directed:
                matrix[dst][src] = 1
        return matrix

    def get_neighbors(self, node_name: str, directed: bool = False) -> List[str]:
        """Return neighbors of a node."""
        neighbors = []
        for nodes in self.links:
            if nodes["source"] == node_name:
                neighbors.append(nodes["target"])
            if not directed and nodes["target"] == node_name:
                neighbors.append(nodes["source"])
        return neighbors

    def has_cycle(self, directed: bool = False) -> bool:
        """Check if the graph contains cycles."""
        if directed:
            return self._has_cycle_directed()
        return self._has_cycle_undirected()

    def _has_cycle_directed(self) -> bool:
        """Detect cycles in a directed graph using DFS."""
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.get_neighbors(node, directed=True):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.names:
            if node not in visited and dfs(node):
                return True
        return False

    def _has_cycle_undirected(self) -> bool:
        """Detect cycles in an undirected graph using DFS."""
        visited = set()

        def dfs(node: str, parent: str | None) -> bool:
            visited.add(node)
            for neighbor in self.get_neighbors(node, directed=False):
                if neighbor not in visited:
                    if dfs(neighbor, node):
                        return True
                elif neighbor != parent:
                    return True
            return False

        for node in self.names:
            if node not in visited and dfs(node, None):
                return True
        return False
