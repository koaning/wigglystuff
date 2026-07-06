from pathlib import Path


def test_liveedit_demo_replaces_grid_sum_with_algorithm_sampler():
    source = Path("demos/liveedit.py").read_text()

    assert "grid_sum" not in source
    for name in ["gcd", "insertion_sort", "first_primes", "sqrt_newton"]:
        assert f"def {name}" in source
        assert f"LiveEdit.inspect_run({name}" in source

