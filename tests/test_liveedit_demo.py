from pathlib import Path


def test_liveedit_demo_wires_functions_through_inspect_run():
    source = Path("demos/liveedit.py").read_text()

    assert "grid_sum" not in source
    for name in ["gcd", "insertion_sort", "binary_search", "gradient_descent"]:
        assert f"def {name}" in source
        assert f"LiveEdit.inspect_run({name}" in source

