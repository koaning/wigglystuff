"""Browser integration tests for TangleLatex."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


NOTEBOOK = str(
    Path(__file__).parent.parent / "fixtures" / "tangle_latex_test_notebook.py"
)
TIMEOUT = 30000 if os.environ.get("CI") else 10000


def drag_without_releasing(page: Page, target, pixels: int = 70):
    target.scroll_into_view_if_needed()
    box = target.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(
        box["x"] + box["width"] / 2 + pixels,
        box["y"] + box["height"] / 2,
        steps=10,
    )


@pytest.mark.e2e
def test_tangle_latex_multi_parameter_interactions(start_marimo, page: Page):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))

    url = start_marimo(NOTEBOOK)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector(".latex-tangle", timeout=TIMEOUT)

    widgets = page.locator(".latex-tangle")
    expect(widgets).to_have_count(3)
    numeric = widgets.nth(0)
    selected_only = widgets.nth(1)
    reveal_all = widgets.nth(2)

    numeric_a = numeric.locator('[data-tangle-param="a"]')
    numeric_b = numeric.locator('[data-tangle-param="b"]')
    expect(numeric_a).to_have_text("2.5")
    expect(numeric_b).to_have_text("1.0")
    expect(numeric.locator(".latex-tangle__reset")).to_be_visible()
    expect(numeric.locator(".latex-tangle__summary")).to_have_count(0)

    drag_without_releasing(page, numeric_a)
    page.mouse.up()
    expect(numeric_a).to_have_text("3.5")
    numeric.locator(".latex-tangle__reset").click()
    expect(numeric_a).to_have_text("2.5")

    selected_a = selected_only.locator('[data-tangle-param="a"]')
    selected_b = selected_only.locator('[data-tangle-param="b"]')
    expect(selected_a).to_have_count(2)
    expect(selected_a).to_have_text(["a", "a"])
    assert (
        selected_a.first.locator(":scope > *").evaluate(
            "element => getComputedStyle(element).boxShadow"
        )
        != "none"
    )
    drag_without_releasing(page, selected_a.first)
    expect(selected_a).to_have_text(["3.5", "3.5"])
    expect(selected_b).to_have_text("b")
    page.mouse.up()
    expect(selected_a).to_have_text(["a", "a"])

    all_a = reveal_all.locator('[data-tangle-param="a"]')
    all_b = reveal_all.locator('[data-tangle-param="b"]')
    drag_without_releasing(page, all_a.first)
    expect(all_a).to_have_text(["3.5", "3.5"])
    expect(all_b).to_have_text("1.0")
    page.mouse.up()
    expect(all_a).to_have_text(["a", "a"])
    expect(all_b).to_have_text("b")

    all_b.click()
    editor = reveal_all.locator(".latex-tangle__editor")
    expect(editor).to_be_visible()
    editor.fill("4.24")
    editor.press("Enter")
    expect(all_b).to_have_text("b")
    expect(page.get_by_text("'b': 4", exact=False)).to_be_visible()

    # A forced widget theme overrides notebook and operating-system preferences.
    expect(numeric_a).to_have_css("color", "rgb(117, 167, 255)")
    expect(numeric_b).to_have_css("color", "rgb(255, 173, 102)")
    expect(numeric.locator(".latex-tangle__reset")).to_have_css(
        "color", "rgb(245, 240, 232)"
    )
    expect(numeric.locator(".latex-tangle__reset")).to_have_css(
        "background-color", "rgb(34, 32, 29)"
    )
    selected_only.evaluate(
        "el => el.parentElement.setAttribute('data-theme', 'dark')"
    )
    expect(selected_a.first).to_have_css("color", "rgb(36, 107, 206)")
    expect(selected_only.locator(".latex-tangle__reset")).to_have_css(
        "color", "rgb(37, 34, 29)"
    )
    expect(selected_only.locator(".latex-tangle__reset")).to_have_css(
        "background-color", "rgb(255, 253, 249)"
    )

    assert not errors, errors
