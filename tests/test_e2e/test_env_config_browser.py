"""Playwright integration test: EnvConfig must not leak manual entries into HTML downloads."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


SECRET_NAME = "WIGGLYSTUFF_EXPORT_SECRET"
SECRET_VALUE = "wigglystuff-secret-red-test-123"
NOTEBOOK = Path(__file__).parent.parent / "fixtures" / "envconfig_export_notebook.py"
ROOT = Path(__file__).parents[2]


@pytest.mark.e2e
def test_env_config_ui_download_omits_manually_entered_secret(
    tmp_path: Path,
    page: Page,
    start_marimo,
):
    """EnvConfig should not leak manually entered values into HTML downloads."""
    notebook_source = NOTEBOOK.read_text(encoding="utf-8")
    assert SECRET_NAME in notebook_source
    assert SECRET_VALUE not in notebook_source

    # Run from the in-tree fixture path so marimo picks up the project's
    # `[tool.marimo.runtime] auto_instantiate = true`. Copying the notebook
    # to tmp_path leaves it without project context and the cells never run.
    env = os.environ.copy()
    env.pop(SECRET_NAME, None)

    url = start_marimo(str(NOTEBOOK), env=env, cwd=ROOT)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector(".env-config-widget", timeout=10_000)

    env_input = page.locator(".env-input")
    env_input.fill(SECRET_VALUE)
    env_input.press("Enter")
    expect(page.locator(".env-config-row")).to_have_attribute(
        "data-status",
        "valid",
        timeout=5_000,
    )
    expect(page.locator("pre", has_text="True")).to_be_visible(timeout=5_000)

    command = page.get_by_text(
        "Download > Download as HTML (exclude code)",
        exact=True,
    )
    for shortcut in ("Meta+K", "Control+K"):
        page.keyboard.press(shortcut)
        try:
            command.wait_for(state="visible", timeout=1_000)
            break
        except PlaywrightTimeoutError:
            page.keyboard.press("Escape")
    else:
        command.wait_for(state="visible", timeout=1_000)

    with page.expect_download(timeout=15_000) as download_info:
        command.click()

    html = Path(download_info.value.path()).read_text(encoding="utf-8")
    assert "True" in html
    assert SECRET_VALUE not in html, (
        "EnvConfig leaked the manually entered secret into the downloaded HTML."
    )
