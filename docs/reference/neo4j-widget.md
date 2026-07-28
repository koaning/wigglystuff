---
title: "Neo4jWidget: explore Neo4j in a notebook"
description: Neo4jWidget runs Cypher queries against a live Neo4j database and explores the resulting graph inside a marimo or Jupyter notebook, expanding nodes on click.
image: neo4j-widget
image_alt: Neo4jWidget showing a Cypher query result as a graph of movie and person nodes joined by ACTED_IN relationships, with label filter chips above
---

# Neo4jWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<div class="wiggly-demo wiggly-demo--static">
<img class="wiggly-demo__poster" src="../assets/gallery/neo4j-widget.webp" alt="Neo4jWidget showing a Cypher query result as a graph of movie and person nodes joined by ACTED_IN relationships, with label filter chips above" decoding="async">
</div>
</div>
<!-- /no-md -->

`Neo4jWidget` takes a `neo4j` driver (or a `uri` plus `auth`), reads the database's
labels, relationship types and property keys up front, and puts a Cypher input above a
graph view of whatever the query returns. Clicking a node runs a follow-up query to
pull in its neighbors, so you can walk outward from a small result instead of writing
ever-longer Cypher. What is on screen stays readable from Python via `nodes`,
`relationships`, `selected_nodes` and `selected_relationships`.

It talks to a real database, so this page has no in-browser demo — [run it on
molab](https://molab.marimo.io/notebooks/nb_ghifaw8nRCuDAgc1UTajXU?utm_source=wigglystuff)
against your own server instead. See also: [GraphWidget](graph-widget.md) for graphs you
build in Python, [EdgeDraw](edge-draw.md) for sketching one by hand, and
[Treemap](treemap.md) for hierarchies rather than graphs.

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
