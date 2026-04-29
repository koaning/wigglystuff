"""Export regression tests for EnvConfig."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


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
