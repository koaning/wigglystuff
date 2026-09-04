"""Tests for the ProgressBar widget's script-mode rich terminal mirror."""

import sys

import pytest

from wigglystuff import ProgressBar
from wigglystuff import html


def test_defaults_and_construction():
    bar = ProgressBar()
    assert bar.value == 0
    assert bar.max_value == 100
    assert bar.color == "#22c55e"
    assert bar.show_text is True


def test_script_mode_mirrors_value_including_backward(monkeypatch):
    pytest.importorskip("rich")
    monkeypatch.setattr(html, "_in_notebook", lambda: False)

    bar = ProgressBar(max_value=50)
    assert bar._rich_enabled is True
    assert bar._rich_progress is None  # created lazily

    bar.value = 10
    assert bar._rich_progress is not None
    assert bar._rich_progress.tasks[0].completed == 10

    bar.value = 40
    assert bar._rich_progress.tasks[0].completed == 40

    # rich uses an absolute `completed`, so the bar can also move backward.
    bar.value = 5
    assert bar._rich_progress.tasks[0].completed == 5

    bar._stop_rich()
    assert bar._rich_progress is None


def test_notebook_mode_has_no_terminal_mirror(monkeypatch):
    monkeypatch.setattr(html, "_in_notebook", lambda: True)

    bar = ProgressBar()
    assert bar._rich_enabled is False

    bar.value = 42  # must not create a terminal display
    assert bar._rich_progress is None


def test_missing_rich_is_a_noop(monkeypatch):
    monkeypatch.setattr(html, "_in_notebook", lambda: False)
    # Setting the module to None makes `import rich` raise ImportError.
    monkeypatch.setitem(sys.modules, "rich", None)

    bar = ProgressBar()
    assert bar._rich_enabled is False

    bar.value = 7  # must not raise even though rich is unavailable
    assert bar._rich_progress is None
