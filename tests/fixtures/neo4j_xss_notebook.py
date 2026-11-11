import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import Neo4jWidget

    PAYLOAD = "<img src=x onerror=window.__xss=1>"

    class FakeNode(dict):
        def __init__(self, element_id, labels, props):
            super().__init__(props)
            self.element_id = element_id
            self.labels = labels

    class FakeRel(dict):
        def __init__(self, element_id, rel_type, start_node, end_node, props):
            super().__init__(props)
            self.element_id = element_id
            self.type = rel_type
            self.start_node = start_node
            self.end_node = end_node

    alice = FakeNode("n1", [PAYLOAD], {"name": "alice", PAYLOAD: PAYLOAD})
    bob = FakeNode("n2", ["Person"], {"name": "bob"})
    knows = FakeRel("r1", PAYLOAD, alice, bob, {"since": PAYLOAD})

    class FakeGraph:
        nodes = [alice, bob]
        relationships = [knows]

    class FakeResult(list):
        def graph(self):
            return FakeGraph()

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def run(self, query, **params):
            if "db.labels" in query:
                return FakeResult([{"label": "Person"}])
            if "db.relationshipTypes" in query:
                return FakeResult([{"relationshipType": "KNOWS"}])
            if "db.propertyKeys" in query:
                return FakeResult([{"propertyKey": "name"}])
            return FakeResult()

    class FakeDriver:
        def session(self, **kwargs):
            return FakeSession()

    widget = mo.ui.anywidget(Neo4jWidget(FakeDriver(), initial_query="MATCH (n) RETURN n"))
    widget
    return


if __name__ == "__main__":
    app.run()
