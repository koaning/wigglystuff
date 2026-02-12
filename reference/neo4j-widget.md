# Neo4jWidget API


 Bases: `AnyWidget`


Interactive Neo4j graph explorer with Cypher query input.



```
from wigglystuff import Neo4jWidget

from neo4j import GraphDatabase
from wigglystuff import Neo4jWidget

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
widget = Neo4jWidget(driver)
widget
```

 Source code in `wigglystuff/neo4j_widget.py`

```
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
```


## clear


```
clear() -> None
```


Clear the graph display and selection.

 Source code in `wigglystuff/neo4j_widget.py`

```
def clear(self) -> None:
    """Clear the graph display and selection."""
    self.nodes = []
    self.relationships = []
    self.selected_nodes = []
    self.selected_relationships = []
    self.error = ""
```


## get_selected_node_data


```
get_selected_node_data() -> List[dict]
```


Return full node dicts for currently selected nodes.

 Source code in `wigglystuff/neo4j_widget.py`

```
def get_selected_node_data(self) -> List[dict]:
    """Return full node dicts for currently selected nodes."""
    selected = set(self.selected_nodes)
    return [n for n in self.nodes if n["element_id"] in selected]
```


## get_selected_relationship_data


```
get_selected_relationship_data() -> List[dict]
```


Return full relationship dicts for currently selected relationships.

 Source code in `wigglystuff/neo4j_widget.py`

```
def get_selected_relationship_data(self) -> List[dict]:
    """Return full relationship dicts for currently selected relationships."""
    selected = set(self.selected_relationships)
    return [r for r in self.relationships if r["element_id"] in selected]
```


## run_query


```
run_query(query: str) -> None
```


Execute a Cypher query and merge results into the graph.

 Source code in `wigglystuff/neo4j_widget.py`

```
def run_query(self, query: str) -> None:
    """Execute a Cypher query and merge results into the graph."""
    self._execute_query(query)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `width` | `int` | Widget width in pixels (default: 800). |
| `height` | `int` | Widget height in pixels (default: 500). |
| `schema` | `dict` | Auto-extracted node labels, relationship types, and property keys. |
| `nodes` | `list` | List of node dicts currently displayed. |
| `relationships` | `list` | List of relationship dicts currently displayed. |
| `error` | `str` | Last error message (empty when no error). |
| `query_running` | `bool` | Whether a query is currently executing. |
| `selected_nodes` | `list` | Element IDs of currently selected nodes. |
| `selected_relationships` | `list` | Element IDs of currently selected relationships. |
