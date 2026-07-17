"""Playwright coverage for CubeWidget's core interaction flow."""

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


NOTEBOOK = str(
    Path(__file__).parent.parent / "fixtures" / "cube_widget_test_notebook.py"
)
TIMEOUT = 30000 if os.environ.get("CI") else 10000


@pytest.mark.e2e
def test_cube_lock_slider_and_reset_flow(start_marimo, page: Page):
    url = start_marimo(NOTEBOOK)
    page.goto(url, wait_until="networkidle")

    root = page.locator(".cube-widget-root")
    expect(root).to_be_visible(timeout=TIMEOUT)
    expect(root.locator(".selection-plane")).to_have_count(0)
    expect(root.locator(".selection-line")).to_have_count(0)
    expect(root.locator(".selection-point")).to_have_count(0)
    expect(root.locator(".cube-svg")).not_to_have_class(
        re.compile(r"has-selection")
    )
    expect(root.locator(".wireframe line").first).to_have_css(
        "stroke-dasharray", "none"
    )
    expect(page.get_by_test_id("cube-state")).to_contain_text("locks=")

    page.evaluate("document.documentElement.classList.add('dark')")
    expect(root.locator(".wireframe line").first).to_have_css(
        "stroke", "rgb(85, 85, 85)"
    )
    page.evaluate("document.documentElement.classList.remove('dark')")

    root.locator(".axis-x .axis-label-bg").click()
    expect(root.locator(".selection-plane")).to_have_count(1)
    expect(root.locator(".cube-svg")).to_have_class(
        re.compile(r"has-selection")
    )
    expect(root.locator(".wireframe line").first).to_have_css(
        "stroke-dasharray", "4px, 5px"
    )
    assert root.locator(".wireframe line").evaluate_all(
        "lines => new Set(lines.map(line => getComputedStyle(line).strokeDasharray)).size"
    ) == 1
    expect(root.locator(".axis-cutout")).to_have_count(3)
    expect(root.locator(".axis-line")).to_have_count(3)
    expect(root.locator(".axis-line").first).to_have_css(
        "stroke-dasharray", "none"
    )

    page.evaluate("document.documentElement.classList.add('dark')")
    expect(root.locator(".axis-cutout").first).to_have_css(
        "stroke", "rgb(36, 36, 36)"
    )
    page.evaluate("document.documentElement.classList.remove('dark')")

    x_row = root.locator(".slider-row[data-axis='x']")
    expect(x_row).to_be_visible()
    expect(x_row.locator(".slider-label")).to_have_text("Angle")
    expect(x_row.locator("input")).to_have_attribute("max", "90")
    expect(x_row.locator("input")).to_have_css(
        "background-image", re.compile(r"linear-gradient")
    )
    assert x_row.locator("input").evaluate(
        "slider => getComputedStyle(slider).getPropertyValue('--slider-color').trim()"
    ) == "#e74c3c"
    expect(page.get_by_test_id("cube-state")).to_contain_text("locks=x")
    expect(page.get_by_test_id("cube-state")).to_contain_text("plane=Angle")

    page.get_by_role("button", name="Update X axis").click()
    expect(x_row.locator(".slider-label")).to_have_text("Bearing")
    expect(x_row.locator("input")).to_have_attribute("max", "180")
    expect(x_row.locator("input")).to_have_attribute("step", "1.8")

    root.locator(".axis-y .axis-label-bg").click()
    expect(root.locator(".selection-line")).to_have_count(1)
    expect(root.locator(".selection-line .selection-cutout")).to_have_count(1)
    expect(root.locator(".selection-line .selection-mark")).to_have_count(1)
    expect(page.get_by_test_id("cube-state")).to_contain_text("locks=x,y")
    expect(page.get_by_test_id("cube-state")).to_contain_text("line=Force")

    root.locator(".axis-z .axis-label-bg").click()
    expect(root.locator(".selection-point")).to_have_count(1)
    expect(root.locator(".selection-point circle")).to_have_attribute("r", "5.5")
    assert root.locator(".cube-svg").evaluate(
        "svg => [...svg.children].map(node => node.getAttribute('class'))"
    ) == [
        "wireframe",
        "axis axis-x",
        "axis axis-y",
        "axis axis-z",
        "selection-plane",
        "selection-line",
        "selection-point",
        "axis-badges",
    ]
    expect(page.get_by_test_id("cube-state")).to_contain_text("locks=x,y,z")
    expect(page.get_by_test_id("cube-state")).to_contain_text("point=Time")

    x_slider = root.locator(".slider-row[data-axis='x'] input")
    x_slider.evaluate(
        """slider => {
            slider.value = "75.6";
            slider.dispatchEvent(new Event("input", { bubbles: true }));
        }"""
    )
    expect(page.get_by_test_id("cube-state")).to_contain_text("x=75.6")

    root.locator(".reset-button").click()
    expect(root.locator(".cube-svg")).not_to_have_class(
        re.compile(r"has-selection")
    )
    expect(root.locator(".wireframe line").first).to_have_css(
        "stroke-dasharray", "none"
    )
    expect(root.locator(".selection-plane")).to_have_count(0)
    expect(root.locator(".selection-line")).to_have_count(0)
    expect(root.locator(".selection-point")).to_have_count(0)
    expect(root.locator(".slider-row")).to_have_count(0)
    expect(page.get_by_test_id("cube-state")).to_have_text(
        re.compile(r"^locks=;")
    )
