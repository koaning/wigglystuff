# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.19.11",
#     "numpy==2.4.2",
#     "polars==1.30.0",
#     "scikit-learn==1.8.0",
# ]
# ///

import marimo

__generated_with = "0.21.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import altair as alt
    import numpy as np
    import polars as pl
    from sklearn.linear_model import HuberRegressor

    return HuberRegressor, alt, np, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Forecast Chart

    A simple function that takes a time series DataFrame and produces an Altair
    chart with a robust exponential fit projected into the future.
    """)
    return


@app.cell
def _(HuberRegressor, alt, np, pl):
    def forecast_chart(
        df: pl.DataFrame,
        date_col: str,
        value_col: str,
        fit_window: int = 180,
        projection_days: int = 365,
        title: str | None = None,
        width: int | None = None,
        height: int = 400,
    ) -> alt.Chart:
        """Create a time series chart with an exponential forecast.

        Fits y = a * b^x via log-linear regression (Huber loss for robustness)
        on the last `fit_window` data points and projects forward.

        Args:
            df: A Polars DataFrame with at least a date column and a value column.
            date_col: Name of the date column.
            value_col: Name of the numeric value column.
            fit_window: Number of most-recent data points to use for the fit.
            projection_days: How many days to project into the future.
            title: Optional chart title.
            width: Chart width in pixels. If None, fills the container width.
            height: Chart height in pixels (default 400).

        Returns:
            An interactive Altair chart with actual data (solid) and
            forecast (dashed).
        """
        dates = df[date_col].to_numpy()
        values = df[value_col].to_numpy().astype(float)

        # Clamp fit window to available data
        fit_window = min(fit_window, len(values))

        # Robust exponential fit on the tail
        X_fit = np.arange(fit_window).reshape(-1, 1)
        regressor = HuberRegressor().fit(X_fit, np.log(values[-fit_window:]))

        # Weekly growth rate
        growth_rate = (np.exp(regressor.coef_[0] * 7) - 1) * 100

        # Build projection dates
        dates_proj = np.concatenate([
            dates[-fit_window:],
            dates[-1] + np.arange(1, projection_days + 1, dtype="timedelta64[D]"),
        ])
        X_proj = np.arange(len(dates_proj)).reshape(-1, 1)
        fitted = np.exp(regressor.predict(X_proj))

        df_fit = pl.DataFrame({
            "date": dates_proj,
            "fitted": fitted,
            "growth": f"{growth_rate:+.1f}%/wk",
        })

        # Axes extend to cover the full projection
        default_end = dates[-1] + np.timedelta64(projection_days, "D")
        y_max = float(max(values.max(), fitted.max())) * 1.1

        actual_chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X(
                    f"{date_col}:T",
                    scale=alt.Scale(domain=[
                        dates[0].astype(str),
                        default_end.astype(str),
                    ]),
                ),
                y=alt.Y(
                    f"{value_col}:Q",
                    title=value_col,
                    scale=alt.Scale(domain=[0, y_max]),
                ),
                color=alt.value("#1f77b4"),
                tooltip=[
                    alt.Tooltip(f"{date_col}:T", title="Date", format="%Y-%m-%d"),
                    alt.Tooltip(f"{value_col}:Q", title=value_col, format=",.0f"),
                ],
            )
        )

        fit_chart = (
            alt.Chart(df_fit)
            .mark_line(strokeDash=[5, 5])
            .encode(
                x=alt.X(
                    "date:T",
                    scale=alt.Scale(domain=[
                        dates[0].astype(str),
                        default_end.astype(str),
                    ]),
                ),
                y=alt.Y(
                    "fitted:Q",
                    scale=alt.Scale(domain=[0, y_max]),
                ),
                color=alt.Color(
                    "growth:N",
                    scale=alt.Scale(range=["#ff7f0e"]),
                    legend=alt.Legend(title=None),
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                    alt.Tooltip("fitted:Q", title="Forecast", format=",.0f"),
                    alt.Tooltip("growth:N", title="Growth Rate"),
                ],
            )
        )

        props = {
            "height": height,
            "usermeta": {"embedOptions": {"actions": False}},
        }
        if width is not None:
            props["width"] = width
        if title:
            props["title"] = title

        chart = (
            (actual_chart + fit_chart)
            .properties(**props)
            .interactive(bind_y=False)
        )
        return chart

    return (forecast_chart,)


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
        width=800,
        height=200
    )
    return


if __name__ == "__main__":
    app.run()
