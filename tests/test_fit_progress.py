import warnings

import pytest

pytest.importorskip("sklearn.callback")  # scikit-learn 1.9+

from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

import wigglystuff.fit_progress as fit_progress
from wigglystuff import FitProgress

X, y = make_classification(n_samples=300, n_features=10, random_state=0)


@pytest.fixture
def in_notebook(monkeypatch):
    monkeypatch.setattr(fit_progress, "_in_notebook", lambda: True)


def fit_quietly(progress, search):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return progress.fit(search, X, y)


def cells(progress):
    return [t for t in progress.tasks if (t["source_task"] or t["task"]) == "candidate-split-evaluation"]


@pytest.mark.parametrize("n_jobs", [None, 2])
def test_grid_search_streams_progress_and_live_scores(in_notebook, n_jobs):
    progress = FitProgress()
    search = GridSearchCV(LogisticRegression(max_iter=5), {"C": [0.01, 1.0]}, cv=3, n_jobs=n_jobs)
    fitted = fit_quietly(progress, search)

    assert fitted is search
    assert progress.status == "done"
    assert progress.candidates == [{"C": "0.01"}, {"C": "1"}]
    fits = cells(progress)
    assert len(fits) == 6
    assert all(f["state"] == "done" and f["unit"] == "lbfgs-iter" for f in fits)
    assert fits[0]["params"] == {"C": "0.01"} and fits[0]["max_iter"] == 5
    # The per-fold test scores sent live match cv_results_.
    live = [f["score"] for f in sorted(fits, key=lambda f: f["path"])]
    assert live == [score for row in progress.scores["folds"] for score in row]
    assert progress.scores["best_index"] == search.best_index_
    assert progress.scores["rank"] == list(search.cv_results_["rank_test_score"])
    # Nothing of the widget is left on the fitted search.
    assert getattr(search, "_skl_callbacks", []) == []
    assert search.scoring is None
    assert not isinstance(search.scorer_, fit_progress._ScoreReporter)
    search.score(X, y)


def test_estimator_without_callbacks_and_multimetric_scoring(in_notebook):
    progress = FitProgress()
    search = GridSearchCV(
        RandomForestClassifier(n_estimators=3, random_state=0),
        {"max_depth": [2, 4]},
        cv=2,
        scoring=["accuracy", "f1"],
        refit="f1",
    )
    fit_quietly(progress, search)

    # A random forest reports no progress of its own, but each fit still gets
    # a cell. Multi-metric scores only arrive at the end, for the refit metric.
    fits = cells(progress)
    assert len(fits) == 4 and all(f["state"] == "done" for f in fits)
    assert not any("score" in f for f in fits)
    assert progress.scores["metric"] == "f1"
    assert progress.candidates == [{"max_depth": "2"}, {"max_depth": "4"}]
    assert search.scoring == ["accuracy", "f1"]


def test_failed_fit_keeps_estimator_clean(in_notebook):
    progress = FitProgress()
    search = GridSearchCV(LogisticRegression(), {"C": [-1.0]}, cv=2, error_score="raise")
    with pytest.raises(ValueError):
        fit_quietly(progress, search)
    assert progress.status == "error"
    assert getattr(search, "_skl_callbacks", []) == []
    assert search.scoring is None


@pytest.mark.parametrize("n_jobs", [None, 2])
def test_forest_search_does_not_warn_about_callback_support(in_notebook, n_jobs):
    progress = FitProgress()
    search = GridSearchCV(
        RandomForestClassifier(n_estimators=3, random_state=0),
        {"max_depth": [2, 4]},
        cv=2,
        n_jobs=n_jobs,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        progress.fit(search, X, y)

    # A random forest can't receive the propagated callback; sklearn would
    # otherwise warn about that once per fold fit and once for the refit.
    assert not [w for w in caught if "does not support callbacks" in str(w.message)]
    assert progress.status == "done"


def test_script_mode_forest_search_does_not_warn_about_callback_support(monkeypatch):
    pytest.importorskip("rich")
    monkeypatch.setattr(fit_progress, "_in_notebook", lambda: False)
    progress = FitProgress()
    search = GridSearchCV(
        RandomForestClassifier(n_estimators=3, random_state=0),
        {"max_depth": [2, 4]},
        cv=2,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        progress.fit(search, X, y)

    assert not [w for w in caught if "does not support callbacks" in str(w.message)]


def test_script_mode_fits_without_the_widget(monkeypatch):
    monkeypatch.setattr(fit_progress, "_in_notebook", lambda: False)
    progress = FitProgress()
    model = LogisticRegression(max_iter=5)
    assert fit_quietly(progress, model) is model
    assert hasattr(model, "coef_")
    assert progress.tasks == [] and progress.status == "idle"
    assert getattr(model, "_skl_callbacks", []) == []


def test_validation():
    with pytest.raises(ValueError):
        FitProgress(max_propagation_depth=-1)
    with pytest.raises(ValueError):
        FitProgress(sync_throttle_ms=-1)
    with pytest.raises(TypeError, match="does not support scikit-learn callbacks"):
        FitProgress().fit(object(), X, y)
    assert FitProgress(color="tomato").color == "tomato"
