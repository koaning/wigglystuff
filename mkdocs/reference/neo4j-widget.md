# Neo4jWidget API

::: wigglystuff.neo4j_widget.Neo4jWidget

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
