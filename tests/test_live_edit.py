import pytest
from pathlib import Path

from wigglystuff.live_edit import LiveEdit, inspect_run


def binary_search(key, array):
    low = 0
    high = len(array) - 1

    while low <= high:
        mid = (low + high) // 2
        value = array[mid]
        if value < key:
            low = mid + 1
        elif value > key:
            high = mid - 1
        else:
            return mid

    return -1


def grid_sum(rows, cols):
    total = 0
    for r in range(rows):
        rowbase = r * 100
        for c in range(cols):
            total = total + rowbase + c

    return total


def test_inspect_run_traces_binary_search_top_to_bottom():
    widget = LiveEdit.inspect_run(binary_search, key="d", array=list("abcdef"))

    assert widget.error is None
    assert widget.trace["setup"] == [
        {"name": "key", "repr": "'d'"},
        {"name": "array", "repr": "['a', 'b', 'c', 'd', 'e', 'f']"},
        {"name": "low", "repr": "0"},
        {"name": "high", "repr": "5"},
    ]

    loop = widget.trace["body"][0]
    assert loop["kind"] == "loop"
    assert loop["loop_type"] == "while"
    assert loop["columns"] == ["low", "high", "mid", "value"]
    assert loop["passes"] == [
        {
            "cells": {"mid": "2", "value": "'c'", "low": "3", "high": "5"},
            "changed": ["mid", "value", "low"],
            "children": [],
        },
        {
            "cells": {"mid": "4", "value": "'e'", "low": "3", "high": "3"},
            "changed": ["mid", "value", "high"],
            "children": [],
        },
        {
            "cells": {"mid": "3", "value": "'d'", "low": "3", "high": "3"},
            "changed": ["mid", "value"],
            "children": [],
        },
    ]
    assert widget.trace["returned"] == {"repr": "3"}


def test_nested_loops_attach_child_trace_to_outer_pass():
    widget = LiveEdit.inspect_run(grid_sum, rows=2, cols=3)

    assert widget.error is None
    outer = widget.trace["body"][0]
    assert outer["loop_type"] == "for"
    assert outer["columns"] == ["r", "rowbase"]
    assert len(outer["passes"]) == 2

    first_inner = outer["passes"][0]["children"][0]
    assert first_inner["columns"] == ["c", "total"]
    assert first_inner["passes"] == [
        {"cells": {"c": "0", "total": "0"}, "changed": ["c", "total"], "children": []},
        {"cells": {"c": "1", "total": "1"}, "changed": ["c", "total"], "children": []},
        {"cells": {"c": "2", "total": "3"}, "changed": ["c", "total"], "children": []},
    ]

    second_inner = outer["passes"][1]["children"][0]
    assert second_inner["passes"][-1]["cells"] == {"c": "2", "total": "306"}
    assert widget.trace["returned"] == {"repr": "306"}


def test_nested_loop_annotations_use_trace_loop_ids():
    widget = LiveEdit.inspect_run(grid_sum, rows=2, cols=3)

    outer = widget.trace["body"][0]
    inner = outer["passes"][0]["children"][0]
    annotation_ids = [loop["loop_id"] for loop in widget.annotations["loops"]]

    assert annotation_ids == [outer["loop_id"], inner["loop_id"]]
    assert any(
        line["loop_body"] == [outer["loop_id"], inner["loop_id"]]
        for line in widget.annotations["lines"]
    )


def test_annotations_include_python_syntax_tokens():
    widget = LiveEdit.inspect_run(binary_search, key="d", array=list("abcdef"))

    def_line = widget.annotations["lines"][0]["tokens"]
    low_line = widget.annotations["lines"][1]["tokens"]

    assert {"type": "kw", "start": 0, "end": 3} in def_line
    assert {"type": "fn", "start": 4, "end": 17} in def_line
    assert {"type": "var", "name": "key", "start": 18, "end": 21} in def_line
    assert {"type": "var", "name": "array", "start": 23, "end": 28} in def_line
    assert {"type": "num", "start": 10, "end": 11} in low_line


def test_inspect_run_raises_clear_error_for_builtin():
    with pytest.raises(TypeError, match="Python source"):
        LiveEdit.inspect_run(len)


def test_retrace_reports_argument_mismatch_without_crashing():
    widget = LiveEdit.inspect_run(binary_search, key="d", array=list("abcdef"))

    widget.code = "def binary_search(key):\n    return key\n"

    assert widget.error["type"] == "TypeError"
    assert "arguments" in widget.error["message"]
    assert widget.trace["returned"] is None


def test_module_level_inspect_run_alias():
    from wigglystuff import LiveEdit as RootLiveEdit
    from wigglystuff import inspect_run as root_inspect_run

    widget = inspect_run(binary_search, key="d", array=list("abcdef"))
    root_widget = root_inspect_run(binary_search, key="d", array=list("abcdef"))

    assert isinstance(widget, LiveEdit)
    assert isinstance(root_widget, RootLiveEdit)
    assert widget.editable is False


def test_repr_snapshots_for_in_place_mutation():
    pytest.importorskip("numpy")

    def mutate_array():
        import numpy as np

        values = np.array([0, 0, 0])
        for index in range(3):
            values[index] = index + 1
        return values

    widget = LiveEdit.inspect_run(mutate_array)

    loop = widget.trace["body"][0]
    assert loop["columns"] == ["index", "values"]
    assert [row["cells"]["values"] for row in loop["passes"]] == [
        "array([1, 0, 0])",
        "array([1, 2, 0])",
        "array([1, 2, 3])",
    ]


def test_auto_theme_follows_notebook_not_os_preference():
    css = Path("wigglystuff/static/liveedit.css").read_text()

    assert "prefers-color-scheme" not in css
    assert '.liveedit-root[data-theme="dark"]' in css
    assert '[data-theme="dark"] .liveedit-root[data-theme="auto"]' in css


def test_changed_cells_use_weight_not_red_color():
    css = Path("wigglystuff/static/liveedit.css").read_text()

    changed_rule = css[css.index(".liveedit-changed") : css.index("}", css.index(".liveedit-changed"))]
    assert "--liveedit-changed" not in css
    assert "color: #cf222e" not in changed_rule
    assert "font-weight: 700" in changed_rule
