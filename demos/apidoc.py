# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.2.23",
# ]
# ///

import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # ApiDoc

    Renders API documentation for Python classes and functions directly in a notebook.
    It inspects signatures, docstrings, methods, and properties automatically.
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from wigglystuff import ApiDoc

    return (ApiDoc,)


@app.class_definition
class Estimator:
    """A simple estimator that fits a linear model.

    This estimator demonstrates the ApiDoc widget by providing
    typed parameters, methods with docstrings, and properties.

    **Example:**

    ```python
    est = Estimator(alpha=0.5)
    est.fit([[1, 2], [3, 4]], [0, 1])
    print(est.predict([[5, 6]]))
    ```
    """

    def __init__(self, alpha: float = 1.0, fit_intercept: bool = True, max_iter: int = 100):
        """Create an Estimator.

        Args:
            alpha: Regularization strength.
            fit_intercept: Whether to fit an intercept term.
            max_iter: Maximum number of iterations.
        """
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self._coef = None

    def fit(self, X: list, y: list) -> "Estimator":
        """Fit the model to training data.

        Args:
            X: Training features.
            y: Target values.

        Returns:
            self
        """
        self._coef = [0.0] * len(X[0]) if X else []
        return self

    def predict(self, X: list) -> list:
        """Generate predictions for new data.

        Args:
            X: Input features.

        Returns:
            Predicted values.
        """
        return [0.0] * len(X)

    @property
    def coef(self) -> list:
        """The fitted coefficients after calling fit()."""
        return self._coef

    @classmethod
    def from_config(cls, config: dict) -> "Estimator":
        """Create an estimator from a configuration dictionary.

        Args:
            config: Dictionary of keyword arguments.
        """
        return cls(**config)


@app.cell
def _(ApiDoc, mo):
    mo.ui.anywidget(ApiDoc(Estimator))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `ApiDoc` also works on standalone functions.
    """)
    return


@app.function
def train_model(
    data: list,
    epochs: int = 10,
    learning_rate: float = 0.01,
    *,
    verbose: bool = False,
) -> dict:
    """Train a model on the provided data.

    Runs gradient descent for the given number of epochs and returns
    a dictionary with training history.

    **Args:**
    - `data`: Training samples.
    - `epochs`: Number of training epochs.
    - `learning_rate`: Step size for gradient descent.
    - `verbose`: If True, print progress each epoch.

    Returns:
        A dict with keys 'loss' and 'epochs'.
    """
    return {"loss": 0.0, "epochs": epochs}


@app.cell
def _(ApiDoc):
    ApiDoc(train_model)
    return


if __name__ == "__main__":
    app.run()
