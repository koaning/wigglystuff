import sys
import types

import pytest

from wigglystuff import Neo4jWidget


class FakeGraph:
    nodes = []
    relationships = []


class FakeResult(list):
    def graph(self):
        return FakeGraph()


class FakeSession:
    def __init__(self, driver, kwargs):
        self.driver = driver
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def run(self, query, **params):
        self.driver.runs.append((query, self.kwargs.get("default_access_mode")))
        return FakeResult()


class FakeDriver:
    def __init__(self):
        self.runs = []

    def session(self, **kwargs):
        return FakeSession(self, kwargs)


@pytest.fixture(autouse=True)
def fake_neo4j(monkeypatch):
    module = types.ModuleType("neo4j")
    module.READ_ACCESS = "READ"
    monkeypatch.setitem(sys.modules, "neo4j", module)


def browser_queries(driver):
    return [run for run in driver.runs if not run[0].startswith("CALL db.")]


def test_browser_queries_are_read_only_by_default():
    driver = FakeDriver()
    widget = Neo4jWidget(driver)
    widget._query_request = {"query": "CREATE (n:Test)", "request_id": 1}
    assert browser_queries(driver) == [("CREATE (n:Test)", "READ")]


def test_read_only_false_allows_write_sessions():
    driver = FakeDriver()
    widget = Neo4jWidget(driver, read_only=False)
    widget._query_request = {"query": "CREATE (n:Test)", "request_id": 1}
    assert browser_queries(driver) == [("CREATE (n:Test)", None)]


def test_python_run_query_is_not_restricted():
    driver = FakeDriver()
    widget = Neo4jWidget(driver)
    widget.run_query("CREATE (n:Test)")
    assert browser_queries(driver) == [("CREATE (n:Test)", None)]
