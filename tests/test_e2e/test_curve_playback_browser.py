"""Playwright integration tests for curve playback controls."""

import os
import time

import pytest
from playwright.sync_api import Page, expect


TIMEOUT = 30000 if os.environ.get("CI") else 10000


def _slider_value(page: Page, selector: str) -> float:
    return float(page.locator(selector).first.input_value())


def _wait_for_slider_to_advance(page: Page, selector: str, start: float) -> None:
    deadline = time.monotonic() + TIMEOUT / 1000
    while time.monotonic() < deadline:
        if _slider_value(page, selector) > start:
            return
        page.wait_for_timeout(50)
    raise AssertionError(f"{selector} did not advance beyond {start}")


def _assert_play_pause_stops_progress(
    start_marimo,
    page: Page,
    notebook: str,
    button_selector: str,
    slider_selector: str,
) -> None:
    url = start_marimo(notebook)
    page.goto(url, wait_until="networkidle")

    button = page.locator(button_selector).first
    expect(button).to_be_visible(timeout=TIMEOUT)
    expect(button).to_have_attribute("aria-label", "Play")
    expect(button).to_have_attribute("aria-pressed", "false")

    start_value = _slider_value(page, slider_selector)
    button.click()
    expect(button).to_have_attribute("aria-label", "Pause")
    expect(button).to_have_attribute("aria-pressed", "true")
    _wait_for_slider_to_advance(page, slider_selector, start_value)

    button.click()
    expect(button).to_have_attribute("aria-label", "Play")
    expect(button).to_have_attribute("aria-pressed", "false")

    paused_value = _slider_value(page, slider_selector)
    page.wait_for_timeout(350)
    after_pause = _slider_value(page, slider_selector)
    assert after_pause == pytest.approx(paused_value, abs=0.0005)


@pytest.mark.e2e
def test_bezier_curve_play_pause_button_stops_progress(start_marimo, page: Page):
    _assert_play_pause_stops_progress(
        start_marimo,
        page,
        "demos/beziercurve.py",
        ".bezier-curve-play",
        ".bezier-curve-range",
    )


@pytest.mark.e2e
def test_curve_editor_play_pause_button_stops_progress(start_marimo, page: Page):
    _assert_play_pause_stops_progress(
        start_marimo,
        page,
        "demos/curveeditor.py",
        ".curve-editor-play",
        ".curve-editor-progress",
    )
