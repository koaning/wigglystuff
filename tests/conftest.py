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


@pytest.fixture
def start_marimo():
    """Returns a function that starts a marimo server for a notebook.

    Usage:
        def test_something(start_marimo, page):
            url = start_marimo("demos/sortlist.py")
            page.goto(url)
    """
    servers = []

    def _start(notebook_path: str) -> str:
        port = find_free_port()
        proc = subprocess.Popen(
            [
                "uv", "run", "marimo", "edit",
                "--headless",
                "--no-token",
                "--host", "127.0.0.1",
                "--port", str(port),
                notebook_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        servers.append(proc)

        # Wait for server to start
        url = f"http://127.0.0.1:{port}"
        max_wait = 60 if os.environ.get("CI") else 15
        start = time.time()
        while time.time() - start < max_wait:
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

        time.sleep(2 if os.environ.get("CI") else 1)
        return url

    yield _start

    # Cleanup all servers started during the test
    for proc in servers:
        proc.terminate()
        proc.wait(timeout=5)
