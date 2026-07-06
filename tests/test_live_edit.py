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
            "failed": False,
            "children": [],
        },
        {
            "cells": {"mid": "4", "value": "'e'", "low": "3", "high": "3"},
            "changed": ["mid", "value", "high"],
            "failed": False,
            "children": [],
        },
        {
            "cells": {"mid": "3", "value": "'d'", "low": "3", "high": "3"},
            "changed": ["mid", "value"],
            "failed": False,
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
        {"cells": {"c": "0", "total": "0"}, "changed": ["c", "total"], "failed": False, "children": []},
        {"cells": {"c": "1", "total": "1"}, "changed": ["c", "total"], "failed": False, "children": []},
        {"cells": {"c": "2", "total": "3"}, "changed": ["c", "total"], "failed": False, "children": []},
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


def insertion_sort(values):
    values = values[:]
    for i in range(1, len(values)):
        key = values[i]
        j = i - 1
        while j >= 0 and values[j] > key:
            values[j + 1] = values[j]
            j = j - 1
        values[j + 1] = key
    return values


def test_inspect_run_flags_failing_pass_and_line():
    widget = LiveEdit.inspect_run(insertion_sort, [5, 2, 4, 3, 1, "a"])

    assert widget.error["type"] == "TypeError"
    assert widget.error["lineno"] == 6
    assert widget.trace["returned"] is None

    passes = widget.trace["body"][0]["passes"]
    assert [p["failed"] for p in passes] == [False, False, False, False, True]


def test_default_height_fits_source_with_floor():
    short = LiveEdit("def f(x):\n    return x\n")
    assert short.height == 520

    long_source = (
        "def f(x):\n"
        + "\n".join(f"    x += {i}" for i in range(60))
        + "\n    return x\n"
    )
    tall = LiveEdit(long_source)
    assert tall.height > 520

    assert LiveEdit(long_source, height=300).height == 300


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


def test_numerics_include_only_all_numeric_columns():
    widget = LiveEdit.inspect_run(binary_search, key="d", array=list("abcdef"))

    numerics = widget.trace["body"][0]["numerics"]

    # low/high/mid are numeric every pass; snapshot fallbacks stay numeric too.
    assert numerics == {
        "low": [3.0, 3.0, 3.0],
        "high": [5.0, 3.0, 3.0],
        "mid": [2.0, 4.0, 3.0],
    }
    # `value` holds strings ('c', 'e', 'd') so it is never chartable.
    assert "value" not in numerics


def test_numerics_emitted_for_nested_loops():
    widget = LiveEdit.inspect_run(grid_sum, rows=2, cols=3)

    inner = widget.trace["body"][0]["passes"][0]["children"][0]
    assert inner["numerics"] == {"c": [0.0, 1.0, 2.0], "total": [0.0, 1.0, 3.0]}


def test_float_precision_trims_floats_but_keeps_charts_and_ints_exact():
    def sqrt_newton(x, steps=4):
        guess = x / 2
        for step in range(steps):
            guess = 0.5 * (guess + x / guess)
        return guess

    widget = LiveEdit.inspect_run(sqrt_newton, 30, steps=4, float_precision=4)
    loop = widget.trace["body"][0]

    # Float cells rounded to 4 significant figures; the return chip too.
    assert [pass_["cells"]["guess"] for pass_ in loop["passes"]] == [
        "8.5",
        "6.015",
        "5.501",
        "5.477",
    ]
    assert widget.trace["returned"] == {"repr": "5.477"}
    # Charts keep full precision so plotted lines stay accurate.
    assert loop["numerics"]["guess"][1] == 6.014705882352941
    # Integer columns (step) are untouched by float rounding.
    assert [pass_["cells"]["step"] for pass_ in loop["passes"]] == ["0", "1", "2", "3"]


def test_visible_columns_defaults_to_show_all():
    widget = LiveEdit.inspect_run(binary_search, key="d", array=list("abcdef"))
    assert widget.visible_columns == []

    widget = LiveEdit.inspect_run(
        binary_search, key="d", array=list("abcdef"), visible_columns=["low", "high"]
    )
    assert widget.visible_columns == ["low", "high"]


class _HtmlCell:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return f"Cell({self.n})"

    def _repr_html_(self):
        return f"<b>cell {self.n}</b>"


class _MimeSummary:
    def __init__(self, total):
        self.total = total

    def __repr__(self):
        return f"Summary({self.total})"

    def _mime_(self):
        return ("text/html", f"<div>total={self.total}</div>")


class _Displayable:
    def __repr__(self):
        return "Displayable()"

    def _display_(self):
        return _HtmlCell(99)


def test_rich_html_captured_for_setup_and_return():
    def build(x):
        summary = _MimeSummary(x.n)
        return summary

    widget = LiveEdit.inspect_run(build, _HtmlCell(7))

    setup = {item["name"]: item for item in widget.trace["setup"]}
    assert setup["x"]["html"] == "<b>cell 7</b>"
    assert setup["summary"]["html"] == "<div>total=7</div>"
    assert widget.trace["returned"] == {
        "repr": "Summary(7)",
        "html": "<div>total=7</div>",
    }


def test_rich_html_captured_in_loop_cells_and_display_protocol():
    def scan(cells):
        marker = _Displayable()
        for cell in cells:
            marker = cell
        return marker

    widget = LiveEdit.inspect_run(scan, [_HtmlCell(1), _HtmlCell(2)])

    assert widget.trace["setup"][-1]["html"] == "<b>cell 99</b>"  # _display_ path
    loop = widget.trace["body"][0]
    assert [p["cells_html"]["cell"] for p in loop["passes"]] == [
        "<b>cell 1</b>",
        "<b>cell 2</b>",
    ]


def test_plain_values_stay_repr_only():
    def add(a, b):
        total = a + b
        return total

    widget = LiveEdit.inspect_run(add, 2, 3)

    assert all("html" not in item for item in widget.trace["setup"])
    assert widget.trace["returned"] == {"repr": "5"}


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
