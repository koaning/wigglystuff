from pathlib import Path
from typing import Any, List, Optional

import anywidget
import traitlets


class Neo4jWidget(anywidget.AnyWidget):
    """Interactive Neo4j graph explorer with Cypher query input.

    Examples:
        ```python
        from neo4j import GraphDatabase
        from wigglystuff import Neo4jWidget

        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        widget = Neo4jWidget(driver)
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "neo4j-widget.js"
    _css = Path(__file__).parent / "static" / "neo4j-widget.css"

    width = traitlets.Int(800).tag(sync=True)
    height = traitlets.Int(500).tag(sync=True)
    schema = traitlets.Dict({}).tag(sync=True)
    nodes = traitlets.List([]).tag(sync=True)
    relationships = traitlets.List([]).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)
    query_running = traitlets.Bool(False).tag(sync=True)
    selected_nodes = traitlets.List([]).tag(sync=True)
    selected_relationships = traitlets.List([]).tag(sync=True)
    _query_request = traitlets.Dict({}).tag(sync=True)
    _expand_request = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        driver=None,
        *,
        uri: Optional[str] = None,
        auth: Optional[tuple] = None,
        database: Optional[str] = None,
        width: int = 800,
        height: int = 500,
        max_nodes: int = 300,
        initial_query: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if driver is not None:
            self._driver = driver
        elif uri is not None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(uri, auth=auth)
        else:
            raise ValueError("Provide either a neo4j Driver or uri (+ auth).")
        self._database = database
        self._max_nodes = max_nodes
        schema = self._extract_schema()
        super().__init__(width=width, height=height, schema=schema, **kwargs)
        if initial_query:
            self._execute_query(initial_query)

    def _extract_schema(self) -> dict:
        with self._driver.session(database=self._database) as session:
            labels = [r["label"] for r in session.run("CALL db.labels()")]
            rel_types = [
                r["relationshipType"]
                for r in session.run("CALL db.relationshipTypes()")
            ]
            prop_keys = [
                r["propertyKey"] for r in session.run("CALL db.propertyKeys()")
            ]
        return {
            "labels": labels,
            "relationship_types": rel_types,
            "property_keys": prop_keys,
        }

    @traitlets.observe("_query_request")
    def _on_query_request(self, change: dict) -> None:
        data = change["new"]
        if not data or "query" not in data:
            return
        self._execute_query(data["query"])

    @traitlets.observe("_expand_request")
    def _on_expand_request(self, change: dict) -> None:
        data = change["new"]
        if not data or "element_id" not in data:
            return
        self._expand_node(data["element_id"])

    def _execute_query(self, query: str, merge: bool = False) -> None:
        self.query_running = True
        self.error = ""
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query)
                graph = result.graph()
                new_nodes = self._convert_nodes(graph.nodes)
                new_rels = self._convert_relationships(graph.relationships)
            if merge:
                self._merge_graph(new_nodes, new_rels)
            else:
                self.selected_nodes = []
                self.selected_relationships = []
                self.nodes = new_nodes
                self.relationships = new_rels
        except Exception as e:
            self.error = str(e)
        finally:
            self.query_running = False

    def _expand_node(self, element_id: str) -> None:
        query = "MATCH (n)-[r]-(m) WHERE elementId(n) = $eid RETURN n, r, m"
        self.query_running = True
        self.error = ""
        try:
            with self._driver.session(database=self._database) as session:
                result = session.run(query, eid=element_id)
                graph = result.graph()
                new_nodes = self._convert_nodes(graph.nodes)
                new_rels = self._convert_relationships(graph.relationships)
            self._merge_graph(new_nodes, new_rels)
        except Exception as e:
            self.error = str(e)
        finally:
            self.query_running = False

    def _merge_graph(
        self, new_nodes: List[dict], new_rels: List[dict]
    ) -> None:
        existing_node_ids = {n["element_id"] for n in self.nodes}
        existing_rel_ids = {r["element_id"] for r in self.relationships}

        merged_nodes = list(self.nodes) + [
            n for n in new_nodes if n["element_id"] not in existing_node_ids
        ]
        merged_rels = list(self.relationships) + [
            r for r in new_rels if r["element_id"] not in existing_rel_ids
        ]

        if len(merged_nodes) > self._max_nodes:
            merged_nodes = merged_nodes[: self._max_nodes]
            kept_ids = {n["element_id"] for n in merged_nodes}
            merged_rels = [
                r
                for r in merged_rels
                if r["start_node_element_id"] in kept_ids
                and r["end_node_element_id"] in kept_ids
            ]
            self.error = (
                f"Results truncated to {self._max_nodes} nodes. "
                "Use a LIMIT clause or call clear() first."
            )

        self.nodes = merged_nodes
        self.relationships = merged_rels

    @staticmethod
    def _convert_nodes(neo4j_nodes) -> List[dict]:
        result = []
        for node in neo4j_nodes:
            props = {}
            for k, v in dict(node).items():
                try:
                    props[k] = v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
                except Exception:
                    props[k] = str(v)

            display = ""
            for key in ("name", "title", "label", "id"):
                if key in props and isinstance(props[key], str):
                    display = props[key]
                    break
            if not display:
                for v in props.values():
                    if isinstance(v, str):
                        display = v
                        break

            result.append(
                {
                    "element_id": node.element_id,
                    "labels": list(node.labels),
                    "properties": props,
                    "display": display or str(node.element_id),
                }
            )
        return result

    @staticmethod
    def _convert_relationships(neo4j_rels) -> List[dict]:
        result = []
        for rel in neo4j_rels:
            props = {}
            for k, v in dict(rel).items():
                try:
                    props[k] = v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
                except Exception:
                    props[k] = str(v)

            result.append(
                {
                    "element_id": rel.element_id,
                    "type": rel.type,
                    "start_node_element_id": rel.start_node.element_id,
                    "end_node_element_id": rel.end_node.element_id,
                    "properties": props,
                }
            )
        return result

    def run_query(self, query: str) -> None:
        """Execute a Cypher query and merge results into the graph."""
        self._execute_query(query)

    def get_selected_node_data(self) -> List[dict]:
        """Return full node dicts for currently selected nodes."""
        selected = set(self.selected_nodes)
        return [n for n in self.nodes if n["element_id"] in selected]

    def get_selected_relationship_data(self) -> List[dict]:
        """Return full relationship dicts for currently selected relationships."""
        selected = set(self.selected_relationships)
        return [r for r in self.relationships if r["element_id"] in selected]

    def clear(self) -> None:
        """Clear the graph display and selection."""
        self.nodes = []
        self.relationships = []
        self.selected_nodes = []
        self.selected_relationships = []
        self.error = ""
