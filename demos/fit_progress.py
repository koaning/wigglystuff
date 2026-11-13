# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anywidget",
#     "marimo",
#     "scikit-learn>=1.9",
#     "scipy",
#     "wigglystuff==0.5.40",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import FitProgress

    return FitProgress, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## FitProgress

    scikit-learn 1.9 added **callbacks**: estimators report every task they
    run (each candidate/fold fit of a search, each solver iteration inside it)
    as it happens. The built-in `ProgressBar` callback draws that with `rich`,
    which is great in a terminal but turns into a tall static text block in a
    notebook.

    `FitProgress` draws the same events as a widget. Display it, then fit
    through it with `progress.fit(estimator, X, y)`; you get the fitted
    estimator back, without the callback still attached. Hyperparameter
    searches render as a **candidates × folds grid**: a running cell fills up
    with the solver's iterations, a finished cell shows its test score
    (darker is better), and a row's mean appears once all its folds are in.
    Cells outlined in amber used every iteration (`max_iter`), so they may not
    have converged. Hover any cell for the details.
    """)
    return


@app.cell
def _():
    from scipy.stats import loguniform
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

    X, y = make_classification(
        n_samples=8_000,
        n_features=2_000,
        n_informative=40,
        n_redundant=10,
        n_classes=3,
        flip_y=0.05,
        random_state=42,
    )
    return (
        GridSearchCV,
        LogisticRegression,
        RandomizedSearchCV,
        X,
        loguniform,
        y,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### GridSearchCV

    A real grid: five values of `C` times two values of `class_weight`, four
    folds each, run one fit at a time. The data has far more features than the
    model needs, so weak regularization (large `C`) overfits, and the solver
    also needs every one of its 150 iterations there. Hover a cell for its
    details.
    """)
    return


@app.cell
def _(FitProgress):
    grid_progress = FitProgress()
    grid_progress
    return (grid_progress,)


@app.cell
def _(mo):
    run_grid = mo.ui.run_button(label="Run grid search")
    run_grid
    return (run_grid,)


@app.cell
def _(GridSearchCV, LogisticRegression, X, grid_progress, mo, run_grid, y):
    mo.stop(not run_grid.value)

    grid = grid_progress.fit(
        GridSearchCV(
            LogisticRegression(max_iter=150),
            param_grid={
                "C": [1e-5, 1e-4, 1e-3, 1e-2, 0.1],
                "class_weight": [None, "balanced"],
            },
            cv=4,
        ),
        X,
        y,
    )
    grid.best_params_
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### RandomizedSearchCV

    Twelve random draws of `C` (log-uniform) and `class_weight`, four folds,
    spread over four worker processes with `n_jobs=4`. The fits run in other
    processes but still report back live, so several cells fill at once. This
    one also passes `color="#8250df"`: one CSS color recolors the bars, the
    score shading and the best row.
    """)
    return


@app.cell
def _(FitProgress):
    random_progress = FitProgress(color="#8250df")
    random_progress
    return (random_progress,)


@app.cell
def _(mo):
    run_random = mo.ui.run_button(label="Run randomized search")
    run_random
    return (run_random,)


@app.cell
def _(
    LogisticRegression,
    RandomizedSearchCV,
    X,
    loguniform,
    mo,
    random_progress,
    run_random,
    y,
):
    mo.stop(not run_random.value)

    search = random_progress.fit(
        RandomizedSearchCV(
            LogisticRegression(max_iter=150),
            param_distributions={
                "C": loguniform(1e-5, 1e2),
                "class_weight": [None, "balanced"],
            },
            n_iter=12,
            cv=4,
            n_jobs=4,
            random_state=0,
        ),
        X,
        y,
    )
    search.best_params_
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Other ways of counting progress

    Not every estimator counts iterations. A **Pipeline** reports its steps,
    and its final LogisticRegression still reports lbfgs iterations inside
    them (hover a cell to see both). An estimator **without callback support**,
    like a random forest, reports nothing while it fits: its cells show a
    striped bar until they finish and get their score.
    """)
    return


@app.cell
def _(FitProgress):
    pipe_progress = FitProgress()
    pipe_progress
    return (pipe_progress,)


@app.cell
def _(mo):
    run_pipe = mo.ui.run_button(label="Run pipeline search")
    run_pipe
    return (run_pipe,)


@app.cell
def _(GridSearchCV, LogisticRegression, X, mo, pipe_progress, run_pipe, y):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    mo.stop(not run_pipe.value)

    pipe_search = pipe_progress.fit(
        GridSearchCV(
            make_pipeline(StandardScaler(), LogisticRegression(max_iter=150)),
            param_grid={"logisticregression__C": [1e-3, 1e-2, 0.1, 1.0, 10.0]},
            cv=5,
        ),
        X,
        y,
    )
    pipe_search.best_params_
    return


@app.cell
def _(FitProgress):
    forest_progress = FitProgress(color="seagreen")
    forest_progress
    return (forest_progress,)


@app.cell
def _(mo):
    run_forest = mo.ui.run_button(label="Run random forest search")
    run_forest
    return (run_forest,)


@app.cell
def _(GridSearchCV, X, forest_progress, mo, run_forest, y):
    from sklearn.ensemble import RandomForestClassifier

    mo.stop(not run_forest.value)

    forest_search = forest_progress.fit(
        GridSearchCV(
            RandomForestClassifier(n_estimators=40, n_jobs=-1, random_state=0),
            param_grid={"max_depth": [4, 16], "max_features": ["sqrt", 0.05]},
            cv=3,
        ),
        X,
        y,
    )
    forest_search.best_params_
    return


if __name__ == "__main__":
    app.run()
