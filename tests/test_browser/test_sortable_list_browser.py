"""Playwright integration tests for SortableList widget."""

from playwright.sync_api import Page, expect


def test_sortable_list_renders(start_marimo, page: Page):
    """Test that the SortableList widget renders in the browser."""
    url = start_marimo("demos/sortlist.py")
    page.goto(url, wait_until="networkidle")

    widget = page.locator(".draggable-list-widget")
    expect(widget).to_be_visible()

    items = page.locator(".list-item")
    expect(items).to_have_count(3)  # ["a", "b", "c"]


def test_add_item_updates_list(start_marimo, page: Page):
    """Test that adding an item via the input updates the widget."""
    url = start_marimo("demos/sortlist.py")
    page.goto(url, wait_until="networkidle")

    widget = page.locator(".draggable-list-widget")
    expect(widget).to_be_visible()

    add_input = page.locator(".add-input")
    expect(add_input).to_be_visible()

    add_input.fill("new item")
    add_input.press("Enter")

    items = page.locator(".list-item")
    expect(items).to_have_count(4)

    new_item_label = page.locator(".item-label", has_text="new item")
    expect(new_item_label).to_be_visible()


def test_remove_item_updates_list(start_marimo, page: Page):
    """Test that clicking remove button removes an item."""
    url = start_marimo("demos/sortlist.py")
    page.goto(url, wait_until="networkidle")

    widget = page.locator(".draggable-list-widget")
    expect(widget).to_be_visible()

    items = page.locator(".list-item")
    expect(items).to_have_count(3)

    first_remove = page.locator(".remove-button").first
    first_remove.click()

    expect(items).to_have_count(2)


def test_edit_item_updates_value(start_marimo, page: Page):
    """Test that editing an item updates its value."""
    url = start_marimo("demos/sortlist.py")
    page.goto(url, wait_until="networkidle")

    widget = page.locator(".draggable-list-widget")
    expect(widget).to_be_visible()

    first_label = page.locator(".item-label").first
    first_label.click()

    edit_input = page.locator(".edit-input")
    expect(edit_input).to_be_visible()

    edit_input.fill("edited")
    edit_input.press("Enter")

    edited_label = page.locator(".item-label", has_text="edited")
    expect(edited_label).to_be_visible()


def test_python_state_updates_after_add(start_marimo, page: Page):
    """Test that adding an item updates the Python state visible in the notebook."""
    url = start_marimo("demos/sortlist.py")
    page.goto(url, wait_until="networkidle")

    widget = page.locator(".draggable-list-widget")
    expect(widget).to_be_visible()

    add_input = page.locator(".add-input")
    add_input.fill("python_test")
    add_input.press("Enter")

    page.wait_for_timeout(500)

    # The Python output cell should show the new value
    page.wait_for_selector("text=python_test")
