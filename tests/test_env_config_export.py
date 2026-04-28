"""Export regression tests for EnvConfig."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SECRET_NAME = "WIGGLYSTUFF_EXPORT_SECRET"
SECRET_VALUE = "wigglystuff-secret-red-test-123"
NOTEBOOK = Path(__file__).parent / "fixtures" / "envconfig_export_notebook.py"
ROOT = Path(__file__).parents[1]


def test_env_config_html_export_omits_environment_secret(
    tmp_path: Path,
):
    """EnvConfig should not leak environment values into static HTML exports."""
    notebook_source = NOTEBOOK.read_text(encoding="utf-8")
    assert SECRET_NAME in notebook_source
    assert SECRET_VALUE not in notebook_source

    notebook = tmp_path / NOTEBOOK.name
    shutil.copyfile(NOTEBOOK, notebook)
    output = tmp_path / "export.html"

    env = {**os.environ, SECRET_NAME: SECRET_VALUE}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "marimo",
            "export",
            "html",
            "--no-include-code",
            str(notebook),
            "-o",
            str(output),
            "-f",
        ],
        cwd=Path(__file__).parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    html = output.read_text(encoding="utf-8")

    assert SECRET_VALUE not in html, (
        "EnvConfig leaked the configured secret into the exported HTML."
    )


@pytest.mark.e2e
def test_env_config_ui_download_omits_manually_entered_secret(
    tmp_path: Path,
    page,
    start_marimo,
):
    """EnvConfig should not leak manually entered values into HTML downloads."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import expect

    notebook_source = NOTEBOOK.read_text(encoding="utf-8")
    assert SECRET_NAME in notebook_source
    assert SECRET_VALUE not in notebook_source

    notebook = tmp_path / NOTEBOOK.name
    shutil.copyfile(NOTEBOOK, notebook)
    env = os.environ.copy()
    env.pop(SECRET_NAME, None)

    url = start_marimo(str(notebook), env=env, cwd=ROOT)
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
