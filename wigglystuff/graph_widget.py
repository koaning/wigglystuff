"""GraphWidget -- programmatic force-directed graph visualization."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import anywidget
import traitlets


class GraphWidget(anywidget.AnyWidget):
    """Programmatic force-directed graph widget.

    ``GraphWidget`` renders nodes and edges supplied from Python. Nodes may be
    strings, numbers, or dicts. Edges may be ``(source, target)`` pairs or dicts
    with ``source`` and ``target`` keys.

    Example:
        ``GraphWidget(nodes=["Alpha", "Beta"], edges=[("Alpha", "Beta")])``
    """

    _esm = Path(__file__).parent / "static" / "graph-widget.js"
    _css = Path(__file__).parent / "static" / "graph-widget.css"

    nodes = traitlets.List([]).tag(sync=True)
    edges = traitlets.List([]).tag(sync=True)
    directed = traitlets.Bool(True).tag(sync=True)
    bounded = traitlets.Bool(True).tag(sync=True)
    width = traitlets.Int(800).tag(sync=True)
    height = traitlets.Int(600).tag(sync=True)
    selected_nodes = traitlets.List([]).tag(sync=True)
    selected_edges = traitlets.List([]).tag(sync=True)
    hovered_node = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    def __init__(
        self,
        nodes: Iterable[Any] | None = None,
        edges: Iterable[Any] | None = None,
        *,
        directed: bool = True,
        bounded: bool = True,
        width: int = 800,
        height: int = 600,
        **kwargs: Any,
    ) -> None:
        prepared_nodes = self._coerce_nodes(nodes or [])
        prepared_edges = self._coerce_edges(edges or [], prepared_nodes)
        super().__init__(
            nodes=prepared_nodes,
            edges=prepared_edges,
            directed=directed,
            bounded=bounded,
            width=width,
            height=height,
            **kwargs,
        )

    @staticmethod
    def _stringify(value: Any) -> str:
        return str(value)

    @classmethod
    def _coerce_nodes(cls, nodes: Iterable[Any]) -> list[dict]:
        raw_nodes = list(nodes)
        name_counts = Counter(
            cls._stringify(node["name"])
            for node in raw_nodes
            if isinstance(node, Mapping) and "id" not in node and "name" in node
        )
        scalar_counts = Counter(
            cls._stringify(node) for node in raw_nodes if not isinstance(node, Mapping)
        )
        name_counts.update(scalar_counts)

        normalized = []
        used_ids: set[str] = set()
        for index, node in enumerate(raw_nodes):
            if isinstance(node, Mapping):
                item = dict(node)
                if "id" in item and item["id"] is not None:
                    node_id = cls._stringify(item["id"])
                elif "name" in item and name_counts[cls._stringify(item["name"])] == 1:
                    node_id = cls._stringify(item["name"])
                else:
                    node_id = f"node-{index}"
                if "name" in item and item["name"] is not None:
                    item["name"] = cls._stringify(item["name"])
            else:
                name = cls._stringify(node)
                node_id = name if name_counts[name] == 1 else f"node-{index}"
                item = {"name": name}

            base_id = node_id
            suffix = 1
            while node_id in used_ids:
                node_id = f"{base_id}-{suffix}"
                suffix += 1
            used_ids.add(node_id)
            item["id"] = node_id
            normalized.append(item)
        return normalized

    @classmethod
    def _node_lookup(cls, nodes: Sequence[Mapping[str, Any]]) -> dict[str, str]:
        ids = {cls._stringify(node["id"]) for node in nodes}
        name_counts = Counter(
            cls._stringify(node["name"])
            for node in nodes
            if "name" in node and node["name"] is not None
        )
        lookup = {node_id: node_id for node_id in ids}
        for node in nodes:
            name = node.get("name")
            if name is not None and name_counts[cls._stringify(name)] == 1:
                lookup[cls._stringify(name)] = cls._stringify(node["id"])
        return lookup

    @classmethod
    def _resolve_endpoint(
        cls, endpoint: Any, nodes: Sequence[Mapping[str, Any]], lookup: Mapping[str, str]
    ) -> str:
        key = cls._stringify(endpoint)
        if key in lookup:
            return lookup[key]
        if isinstance(endpoint, int) and 0 <= endpoint < len(nodes):
            return cls._stringify(nodes[endpoint]["id"])
        raise ValueError(f"Unknown graph node endpoint: {endpoint!r}")

    @classmethod
    def _coerce_edges(
        cls, edges: Iterable[Any], nodes: Sequence[Mapping[str, Any]]
    ) -> list[dict]:
        lookup = cls._node_lookup(nodes)
        normalized = []
        used_ids: set[str] = set()
        for index, edge in enumerate(edges):
            if isinstance(edge, Mapping):
                if "source" not in edge or "target" not in edge:
                    raise ValueError("Graph edge dicts must include source and target.")
                item = dict(edge)
            elif isinstance(edge, Sequence) and not isinstance(edge, (str, bytes)) and len(edge) >= 2:
                item = {"source": edge[0], "target": edge[1]}
            else:
                raise ValueError("Graph edges must be dicts or (source, target) pairs.")

            source = cls._resolve_endpoint(item["source"], nodes, lookup)
            target = cls._resolve_endpoint(item["target"], nodes, lookup)
            edge_id = cls._stringify(item.get("id", f"edge-{index}"))
            base_id = edge_id
            suffix = 1
            while edge_id in used_ids:
                edge_id = f"{base_id}-{suffix}"
                suffix += 1
            used_ids.add(edge_id)

            item["id"] = edge_id
            item["source"] = source
            item["target"] = target
            if "name" in item and item["name"] is not None:
                item["name"] = cls._stringify(item["name"])
            normalized.append(item)
        return normalized

    @traitlets.validate("nodes")
    def _validate_nodes(self, proposal: traitlets.Bunch) -> list[dict]:
        return self._coerce_nodes(proposal.value)

    @traitlets.validate("edges")
    def _validate_edges(self, proposal: traitlets.Bunch) -> list[dict]:
        return self._coerce_edges(proposal.value, self.nodes)

    def add_node(
        self,
        name: Any = None,
        *,
        id: Any = None,
        size: int | float | None = None,
        color: str | None = None,
        data: Any = None,
        **attrs: Any,
    ) -> str:
        """Add a node and return its normalized id."""
        node = dict(attrs)
        if id is not None:
            node["id"] = id
        if name is not None:
            node["name"] = name
        if size is not None:
            node["size"] = size
        if color is not None:
            node["color"] = color
        if data is not None:
            node["data"] = data
        new_nodes = self._coerce_nodes([*self.nodes, node])
        self.nodes = new_nodes
        return new_nodes[-1]["id"]

    def remove_node(self, node: Any) -> None:
        """Remove a node by id, unique name, or index, including incident edges."""
        node_id = self._resolve_endpoint(node, self.nodes, self._node_lookup(self.nodes))
        self.detach_node(node_id, delete=True)

    def add_edge(
        self,
        source: Any,
        target: Any,
        *,
        id: Any = None,
        name: Any = None,
        width: int | float | None = None,
        color: str | None = None,
        data: Any = None,
        **attrs: Any,
    ) -> str:
        """Add an edge and return its normalized id."""
        edge = {"source": source, "target": target, **attrs}
        if id is not None:
            edge["id"] = id
        if name is not None:
            edge["name"] = name
        if width is not None:
            edge["width"] = width
        if color is not None:
            edge["color"] = color
        if data is not None:
            edge["data"] = data
        new_edges = self._coerce_edges([*self.edges, edge], self.nodes)
        self.edges = new_edges
        return new_edges[-1]["id"]

    def attach_node(
        self,
        source: Any,
        name: Any = None,
        *,
        id: Any = None,
        edge_id: Any = None,
        edge_name: Any = None,
        size: int | float | None = None,
        color: str | None = None,
        data: Any = None,
        edge_width: int | float | None = None,
        edge_color: str | None = None,
        edge_data: Any = None,
        **attrs: Any,
    ) -> tuple[str, str]:
        """Attach a node to an existing source node.

        If ``id`` or ``name`` resolves to an existing node, only the edge is added.
        Otherwise a new node is created first.

        Returns:
            The normalized ``(node_id, edge_id)`` pair.
        """
        source_id = self._resolve_endpoint(source, self.nodes, self._node_lookup(self.nodes))
        lookup = self._node_lookup(self.nodes)
        node = dict(attrs)
        if id is not None:
            node["id"] = id
        if name is not None:
            node["name"] = name
        if size is not None:
            node["size"] = size
        if color is not None:
            node["color"] = color
        if data is not None:
            node["data"] = data

        node_id = None
        for endpoint in (id, name):
            if endpoint is None:
                continue
            try:
                node_id = self._resolve_endpoint(endpoint, self.nodes, lookup)
                break
            except ValueError:
                pass

        if node_id is None:
            new_nodes = self._coerce_nodes([*self.nodes, node])
            node_id = new_nodes[-1]["id"]
        else:
            updates = dict(attrs)
            if name is not None and id is not None:
                updates["name"] = name
            if size is not None:
                updates["size"] = size
            if color is not None:
                updates["color"] = color
            if data is not None:
                updates["data"] = data
            new_nodes = [
                {**existing, **updates} if existing["id"] == node_id else existing
                for existing in self.nodes
            ]

        edge: dict[str, Any] = {"source": source_id, "target": node_id}
        if edge_id is not None:
            edge["id"] = edge_id
        if edge_name is not None:
            edge["name"] = edge_name
        if edge_width is not None:
            edge["width"] = edge_width
        if edge_color is not None:
            edge["color"] = edge_color
        if edge_data is not None:
            edge["data"] = edge_data

        new_edges = self._coerce_edges([*self.edges, edge], new_nodes)
        edge_id = new_edges[-1]["id"]
        with self.hold_sync():
            self.nodes = new_nodes
            self.edges = new_edges
        return node_id, edge_id

    def detach_node(self, node: Any, *, delete: bool = False) -> None:
        """Remove all edges attached to a node.

        Set ``delete=True`` to remove the node as well.
        """
        node_id = self._resolve_endpoint(node, self.nodes, self._node_lookup(self.nodes))
        new_nodes = [
            n for n in self.nodes if not delete or n["id"] != node_id
        ]
        new_edges = [
            e for e in self.edges if e["source"] != node_id and e["target"] != node_id
        ]
        remaining_edges = {edge["id"] for edge in new_edges}
        with self.hold_sync():
            self.nodes = new_nodes
            self.edges = new_edges
            if delete:
                self.selected_nodes = [n for n in self.selected_nodes if n != node_id]
            self.selected_edges = [
                e for e in self.selected_edges if e in remaining_edges
            ]

    def remove_edge(self, edge: Any) -> None:
        """Remove an edge by id or index."""
        if isinstance(edge, int) and 0 <= edge < len(self.edges):
            edge_id = self.edges[edge]["id"]
        else:
            edge_id = self._stringify(edge)
        self.edges = [e for e in self.edges if e["id"] != edge_id]
        self.selected_edges = [e for e in self.selected_edges if e != edge_id]

    def clear_selection(self) -> None:
        """Clear selected node and edge ids."""
        self.selected_nodes = []
        self.selected_edges = []

    def get_selected_node_data(self) -> list[dict]:
        """Return full node dicts for currently selected nodes."""
        selected = set(self.selected_nodes)
        return [node for node in self.nodes if node["id"] in selected]

    def get_selected_edge_data(self) -> list[dict]:
        """Return full edge dicts for currently selected edges."""
        selected = set(self.selected_edges)
        return [edge for edge in self.edges if edge["id"] in selected]

    def get_adjacency_matrix(self, directed: bool | None = None):
        """Return an adjacency matrix for the current graph."""
        import numpy as np

        if directed is None:
            directed = self.directed
        node_ids = [node["id"] for node in self.nodes]
        index = {node_id: i for i, node_id in enumerate(node_ids)}
        matrix = np.zeros((len(node_ids), len(node_ids)))
        for edge in self.edges:
            if edge["source"] not in index or edge["target"] not in index:
                continue
            src = index[edge["source"]]
            dst = index[edge["target"]]
            matrix[src][dst] = 1
            if not directed:
                matrix[dst][src] = 1
        return matrix
