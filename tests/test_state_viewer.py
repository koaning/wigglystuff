import pytest

from wigglystuff import StateViewer


def solve(board, row, n):
    if row == n:
        return True
    for col in range(n):
        if all(c != col and abs(c - col) != row - r for r, c in enumerate(board)):
            board.append(col)
            if solve(board, row + 1, n):
                return True
            board.pop()
    return False


def show_board(board):
    return f"<pre>{board}</pre>"


def countdown(k):
    while k > 0:
        k -= 1
    return k


def boom(x):
    y = x + 1
    raise RuntimeError("nope")


def test_traces_recursion_with_depth_lines_and_return():
    viewer = StateViewer(solve, show_board, args=([], 0, 4))

    assert viewer.error is None
    assert viewer.truncated is False
    assert viewer.returned == "True"
    assert viewer.code.splitlines()[0] == "def solve(board, row, n):"
    assert viewer.variables == ["board", "row", "n", "col"]
    # One recursion level per queen placed, plus the final `row == n` call.
    assert max(step["depth"] for step in viewer.steps) == 5
    assert viewer.steps[0] == {
        "line": 2,
        "depth": 1,
        "event": "line",
        "view": 0,
        "locals": {"board": "[]", "row": "0", "n": "4"},
    }
    last = viewer.steps[-1]
    assert (last["event"], last["depth"], last["returned"]) == ("return", 1, "True")
    assert viewer.n_steps == len(viewer.steps)
    assert viewer.current == viewer.steps[0]


def test_view_captures_in_place_mutation_and_dedupes():
    viewer = StateViewer(solve, show_board, args=([], 0, 4))

    rendered = [viewer.views[step["view"]] for step in viewer.steps]
    assert rendered[0] == "<pre>[]</pre>"
    assert rendered[-1] == "<pre>[1, 3, 0, 2]</pre>"
    assert len(viewer.views) == len(set(viewer.views)) < viewer.n_steps


def test_view_params_bind_by_name_with_defaults_and_missing_required():
    calls = []

    def view(k, done=None):
        calls.append((k, done))
        return str(k)

    viewer = StateViewer(countdown, view, args=(2,))
    assert calls[0] == (2, None)

    def needs_col(board, col):
        return f"{board}{col}"

    viewer = StateViewer(solve, needs_col, args=([], 0, 4))
    # `col` isn't assigned on the first lines, so no view exists yet.
    assert viewer.steps[0]["view"] == -1
    assert viewer.views[viewer.steps[-1]["view"]] == "[1, 3, 0, 2]1"


def test_max_steps_only_changes_and_validation():
    viewer = StateViewer(solve, show_board, args=([], 0, 6), max_steps=10)
    assert viewer.truncated is True
    assert viewer.n_steps == 10
    assert viewer.returned is None

    viewer = StateViewer(solve, show_board, args=([], 0, 4), only_changes=True)
    views = [step["view"] for step in viewer.steps]
    assert all(a != b for a, b in zip(views, views[1:]))

    with pytest.raises(ValueError):
        StateViewer(solve, show_board, max_steps=0)
    with pytest.raises(TypeError):
        StateViewer(len, show_board)


def test_errors_from_search_and_view_are_reported():
    viewer = StateViewer(boom, lambda y=None: str(y), args=(1,))
    assert viewer.error["source"] == "search_func"
    assert viewer.error["type"] == "RuntimeError"
    assert viewer.error["lineno"] == 3
    assert viewer.steps[-1]["event"] == "raise"

    def broken(k):
        raise ValueError("bad view")

    viewer = StateViewer(countdown, broken, args=(3,))
    assert viewer.error["source"] == "view_func"
    assert viewer.error["message"] == "bad view"
