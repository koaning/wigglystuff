# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.19.11",
#     "numpy==2.4.2",
#     "polars==1.30.0",
#     "scikit-learn==1.8.0",
#     "wigglystuff",
# ]
# ///

import marimo


app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import numpy as np
    import polars as pl

    return np, pl


@app.cell
def _():
    from wigglystuff import forecast_chart

    return (forecast_chart,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Forecast Chart

    A simple function that takes a time series DataFrame and produces an Altair
    chart with a robust exponential fit projected into the future.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Synthetic data demo

    Below is a synthetic daily time series with exponential-ish growth plus noise.
    Use the sliders to adjust the fit window and projection horizon.
    """)
    return


@app.cell
def _(mo):
    fit_window = mo.ui.slider(7, 365, value=90, step=7, label="Fit window (days)")
    projection_days = mo.ui.slider(30, 730, value=365, step=30, label="Projection (days)")
    return fit_window, projection_days


@app.cell
def _(np, pl):
    # Synthetic daily time series: exponential growth + noise + outlier spike
    rng = np.random.default_rng(42)
    n_days = 365
    dates = np.arange("2025-01-01", n_days, dtype="datetime64[D]")
    trend = 100 * np.exp(0.003 * np.arange(n_days))
    noise = rng.normal(0, 8, n_days)
    # Add a 3-week spike around day 300
    spike = np.zeros(n_days)
    spike[300:321] = 150
    values = trend + noise + spike

    df = pl.DataFrame({"date": dates, "value": values})
    return (df,)


@app.cell
def _(fit_window, mo, projection_days):
    mo.hstack([fit_window, projection_days])
    return


@app.cell(hide_code=True)
def _(df, fit_window, forecast_chart, projection_days):
    forecast_chart(
        df,
        date_col="date",
        value_col="value",
        fit_window=fit_window.value,
        projection_days=projection_days.value,
        title="Synthetic metric forecast",
    )
    return


if __name__ == "__main__":
    app.run()
