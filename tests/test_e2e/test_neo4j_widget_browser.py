"""Playwright integration tests for Neo4jWidget."""

import pytest
from playwright.sync_api import Page, expect

PAYLOAD = "<img src=x onerror=window.__xss=1>"


@pytest.mark.e2e
def test_tooltip_renders_properties_as_text(start_marimo, page: Page):
    """Database-supplied labels, keys and values must not be parsed as HTML."""
    url = start_marimo("tests/fixtures/neo4j_xss_notebook.py")
    page.goto(url, wait_until="networkidle")

    tooltip = page.locator(".neo4j-tooltip")

    node = page.locator(".neo4j-node-group").first
    expect(node).to_be_visible()
    node.hover()
    expect(tooltip).to_be_visible()
    expect(tooltip).to_contain_text(f"{PAYLOAD}:")
    expect(tooltip).to_contain_text(f": {PAYLOAD}")
    expect(tooltip.locator("img")).to_have_count(0)

    # Links are thin and move with the force simulation, so fire the event directly.
    page.locator(".neo4j-link").first.dispatch_event("mouseenter")
    expect(tooltip).to_contain_text(f"since: {PAYLOAD}")
    expect(tooltip.locator("img")).to_have_count(0)

    page.wait_for_timeout(500)
    assert page.evaluate("window.__xss") is None
