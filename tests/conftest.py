"""Pytest configuration and fixtures for browser integration tests."""

import os
import subprocess
import time
import socket
import pytest


def find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="function")
def marimo_server(request):
    """Start a marimo server for the specified notebook.

    Usage:
        @pytest.mark.parametrize("marimo_server", ["demos/sortlist.py"], indirect=True)
        def test_something(marimo_server, page):
            page.goto(marimo_server)
            ...
    """
    notebook_path = request.param
    port = find_free_port()

    proc = subprocess.Popen(
        [
            "uv", "run", "marimo", "run",
            "--headless",
            "--host", "127.0.0.1",
            "--port", str(port),
            notebook_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start by polling the port
    # Use longer timeout for CI environments
    url = f"http://127.0.0.1:{port}"
    max_wait = 60 if os.environ.get("CI") else 15
    start = time.time()
    while time.time() - start < max_wait:
        # Check if process died
        if proc.poll() is not None:
            _, stderr = proc.communicate()
            raise RuntimeError(
                f"marimo server exited unexpectedly with code {proc.returncode}. "
                f"stderr: {stderr.decode()}"
            )
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                break
        except (ConnectionRefusedError, socket.timeout):
            time.sleep(0.5)
    else:
        proc.terminate()
        _, stderr = proc.communicate()
        raise RuntimeError(
            f"marimo server failed to start within {max_wait}s. "
            f"stderr: {stderr.decode()}"
        )

    # Give it a bit more time to fully initialize
    time.sleep(2 if os.environ.get("CI") else 1)

    yield url

    proc.terminate()
    proc.wait(timeout=5)
