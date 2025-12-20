from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import anywidget
import numpy as np
import traitlets


class EdgeDraw(anywidget.AnyWidget):
    """Sketch node/link diagrams and sync edges as adjacency-friendly data.

    Examples:
        ```python
        graph = EdgeDraw(names=["A", "B", "C", "D"])
        graph
        ```
    """

    _esm = Path(__file__).parent / "static" / "edgedraw.js"
    _css = Path(__file__).parent / "static" / "edgedraw.css"
    names = traitlets.List([]).tag(sync=True)
    links = traitlets.List([]).tag(sync=True)
    directed = traitlets.Bool(True).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)

    @staticmethod
    def _coerce_links(
        links: Optional[Iterable[Union[Sequence[str], dict]]],
    ) -> List[dict]:
        normalized: List[dict] = []
        if not links:
            return normalized
        for link in links:
            if isinstance(link, dict):
                if "source" in link and "target" in link:
                    normalized.append({"source": link["source"], "target": link["target"]})
                continue
            if isinstance(link, (tuple, list)) and len(link) >= 2:
                normalized.append({"source": link[0], "target": link[1]})
        return normalized

    @traitlets.validate("links")
    def _validate_links(self, proposal: traitlets.Bunch) -> List[dict]:
        return self._coerce_links(proposal.value)

    @staticmethod
    def _iter_links(
        links: Iterable[dict],
    ) -> Iterable[Tuple[str, str]]:
        for link in links:
            yield link["source"], link["target"]

    def __init__(
        self,
        names: List[str],
        height: int = 400,
        width: int = 600,
        directed: bool = True,
        links: Optional[Iterable[Union[Sequence[str], dict]]] = None,
    ) -> None:
        """Create an EdgeDraw widget.

        Args:
            names: Ordered list of node labels.
            height: Canvas height in pixels.
            width: Canvas width in pixels.
            directed: Whether to draw directed edges with arrowheads.
            links: Optional list of (source, target) pairs to seed the widget.
        """
        super().__init__(
            names=names,
            height=height,
            width=width,
            directed=directed,
            links=self._coerce_links(links),
        )

    def get_adjacency_matrix(self, directed: bool = False) -> np.ndarray:
        """Create an adjacency matrix from links and node names."""
        num_nodes = len(self.names)
        matrix = np.zeros((num_nodes, num_nodes))
        for source, target in self._iter_links(self._coerce_links(self.links)):
            src = self.names.index(source)
            dst = self.names.index(target)
            matrix[src][dst] = 1
            if not directed:
                matrix[dst][src] = 1
        return matrix

    def get_neighbors(self, node_name: str, directed: bool = False) -> List[str]:
        """Return neighbors of a node."""
        neighbors = []
        for source, target in self._iter_links(self._coerce_links(self.links)):
            if source == node_name:
                neighbors.append(target)
            if not directed and target == node_name:
                neighbors.append(source)
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

        def dfs(node: str, parent: Optional[str]) -> bool:
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
