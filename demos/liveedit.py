# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "anywidget",
#     "drawdata",
#     "marimo",
#     "wigglystuff==0.5.12",
# ]
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="full")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import LiveEdit

    return LiveEdit, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## LiveEdit

    `LiveEdit.inspect_run(...)` records one run of a Python function and shows
    how loop variables change pass by pass. Hover a variable or loop in either
    panel to connect the code with the trace.
    """)
    return


@app.function
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


@app.cell
def _(LiveEdit, mo):
    binary_trace = mo.ui.anywidget(
        LiveEdit.inspect_run(binary_search, key="g", array=list("abcdef123487561983274132412g"))
    )
    binary_trace
    return


@app.cell
def _(LiveEdit):
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a


    LiveEdit.inspect_run(gcd, 21 * 192, 21 * 7)
    return


@app.cell
def _(LiveEdit):
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


    LiveEdit.inspect_run(insertion_sort, [5, 2, 4, 3, 1])
    return


@app.cell
def _(LiveEdit):
    def first_primes(limit):
        primes = []
        for n in range(2, limit + 1):
            is_prime = True
            for p in primes:
                if n % p == 0:
                    is_prime = False
                    break
            if is_prime:
                primes = primes + [n]
        return primes


    LiveEdit.inspect_run(first_primes, 12)
    return


@app.cell
def _(LiveEdit):
    def sqrt_newton(x, steps=5):
        guess = x / 2
        for step in range(steps):
            guess = 0.5 * (guess + x / guess)
        return guess


    LiveEdit.inspect_run(sqrt_newton, 30, steps=15)
    return


if __name__ == "__main__":
    app.run()
