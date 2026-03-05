"""Playwright integration tests for Tangle widgets."""

from playwright.sync_api import Page, expect


def test_tangle_slider_renders(start_marimo, page: Page):
    """Test that the TangleSlider widget renders in the browser."""
    url = start_marimo("demos/tangle.py")
    page.goto(url, wait_until="networkidle")

    # Wait for anywidget JS to mount
    page.wait_for_selector(".tangle-value", timeout=10000)

    widget = page.locator(".tangle-value").first
    expect(widget).to_be_visible()
    # The first TangleSlider has suffix=" coffees" and amount=10
    expect(widget).to_contain_text("coffees")


def test_tangle_slider_drag_updates_value(start_marimo, page: Page):
    """Test that dragging the TangleSlider changes its displayed value."""
    url = start_marimo("demos/tangle.py")
    page.goto(url, wait_until="networkidle")

    widget = page.locator(".tangle-value").first
    expect(widget).to_be_visible()

    initial_text = widget.text_content()

    # Drag right to increase the value
    box = widget.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 50, box["y"] + box["height"] / 2)
    page.mouse.up()

    page.wait_for_timeout(200)
    new_text = widget.text_content()
    assert new_text != initial_text, f"Value did not change after drag: {initial_text}"


def test_tangle_choice_renders_and_cycles(start_marimo, page: Page):
    """Test that TangleChoice renders and clicking cycles through choices."""
    url = start_marimo("demos/tangle.py")
    page.goto(url, wait_until="networkidle")

    # TangleChoice is the emoji widget with choices ["🙂", "🎉", "💥"]
    choice_widget = page.locator(".tangle-value", has_text="🙂")
    expect(choice_widget).to_be_visible()

    choice_widget.click()
    page.wait_for_timeout(200)

    # After clicking, it should cycle to the next choice
    cycled = page.locator(".tangle-value", has_text="🎉")
    expect(cycled).to_be_visible()


def test_tangle_select_renders(start_marimo, page: Page):
    """Test that TangleSelect renders a select element."""
    url = start_marimo("demos/tangle.py")
    page.goto(url, wait_until="networkidle")

    select = page.locator(".tangle-container select")
    expect(select).to_be_visible()
