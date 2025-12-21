# EdgeDraw API


 Bases: `AnyWidget`


Sketch node/link diagrams and sync edges as adjacency-friendly data.


Examples:


```
graph = EdgeDraw(names=["A", "B", "C", "D"])
graph
```


Create an EdgeDraw widget.


Parameters:


**

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `names` | `List[str]` | Ordered list of node labels. | required |
| `height` | `int` | Canvas height in pixels. | `400` |
| `width` | `int` | Canvas width in pixels. | `600` |
| `directed` | `bool` | Whether to draw directed edges with arrowheads. | `True` |
| `links` | `Optional[Iterable[Union[Sequence[str], dict]]]` | Optional list of (source, target) pairs to seed the widget. | `None` |

 Source code in `wigglystuff/edge_draw.py`

```
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
```


## get_adjacency_matrix


```
get_adjacency_matrix(directed: bool = False) -> ndarray
```


Create an adjacency matrix from links and node names.

 Source code in `wigglystuff/edge_draw.py`

```
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
```


## get_neighbors


```
get_neighbors(
    node_name: str, directed: bool = False
) -> List[str]
```


Return neighbors of a node.

 Source code in `wigglystuff/edge_draw.py`

```
def get_neighbors(self, node_name: str, directed: bool = False) -> List[str]:
    """Return neighbors of a node."""
    neighbors = []
    for source, target in self._iter_links(self._coerce_links(self.links)):
        if source == node_name:
            neighbors.append(target)
        if not directed and target == node_name:
            neighbors.append(source)
    return neighbors
```


## has_cycle


```
has_cycle(directed: bool = False) -> bool
```


Check if the graph contains cycles.

 Source code in `wigglystuff/edge_draw.py`

```
def has_cycle(self, directed: bool = False) -> bool:
    """Check if the graph contains cycles."""
    if directed:
        return self._has_cycle_directed()
    return self._has_cycle_undirected()
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `names` | `list[str]` | Ordered node labels. |
| `links` | `list[dict]` | Link dicts with `source` and `target` keys. |
| `directed` | `bool` | Draw directed edges when true. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
