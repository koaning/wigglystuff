from __future__ import annotations

import base64
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable


def altair2svg(chart: Any) -> str:
    """Convert an Altair chart to SVG format.

    Args:
        chart: An Altair chart object.

    Returns:
        str: The SVG representation of the chart as a string.

    Note:
        This function writes to disk temporarily as Altair doesn't provide
        an in-memory API for SVG conversion.
    """
    # Need to write to disk to get SVG, filetype determines how to store it
    # have not found an api in altair that can return a variable in memory
    with TemporaryDirectory() as tmp_dir:
        chart.save(Path(tmp_dir) / "example.svg")
        return (Path(tmp_dir) / "example.svg").read_text()

def refresh_matplotlib(func: Callable[..., Any]) -> Callable[..., str]:
    """Decorator to convert matplotlib plotting functions to base64-encoded images.

    This decorator wraps a matplotlib plotting function and returns a base64-encoded
    data URI that can be used with ImageRefreshWidget for live updates.

    Args:
        func: A function that creates matplotlib plots using plt commands.

    Returns:
        callable: A wrapper function that returns a base64-encoded JPEG data URI.

    Example:
        >>> @refresh_matplotlib
        ... def plot_sine(x):
        ...     plt.plot(x, np.sin(x))
        ...
        >>> widget = ImageRefreshWidget()
        >>> widget.src = plot_sine(np.linspace(0, 2*np.pi, 100))
    """
    import matplotlib
    import matplotlib.pylab as plt

    matplotlib.use("Agg")

    def wrapper(*args, **kwargs):
        # Reset the figure to prevent accumulation. Maybe we need a setting for this?
        fig = plt.figure()

        # Run function as normal
        func(*args, **kwargs)

        # Store it as base64 and put it into an image.
        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format="jpg")
        my_stringIObytes.seek(0)
        my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()

        # Close the figure to prevent memory leaks
        plt.close(fig)
        plt.close("all")
        return f"data:image/jpg;base64, {my_base64_jpgData}"

    return wrapper


def refresh_altair(func: Callable[..., Any]) -> Callable[..., str]:
    """Decorator to convert Altair chart functions to SVG strings.

    This decorator wraps a function that returns an Altair chart and converts
    the chart to an SVG string that can be used with HTMLRefreshWidget for live updates.

    Args:
        func: A function that returns an Altair chart object.

    Returns:
        callable: A wrapper function that returns an SVG string representation of the chart.

    Example:
        >>> @refresh_altair
        ... def create_chart(data):
        ...     return alt.Chart(data).mark_bar().encode(x='x', y='y')
        ...
        >>> widget = HTMLRefreshWidget()
        >>> widget.html = create_chart(df)
    """

    def wrapper(*args, **kwargs):
        # Run function as normal
        altair_chart = func(*args, **kwargs)
        return altair2svg(altair_chart)

    return wrapper


def forecast_chart(
    df,
    date_col: str,
    value_col: str,
    fit_window: int = 180,
    projection_days: int = 365,
    title: str | None = None,
    width: int | str | None = None,
    height: int = 400,
):
    """Create a time series chart with an exponential forecast.

    Fits y = a * b^x via log-linear regression (Huber loss for robustness)
    on the last ``fit_window`` data points and projects forward.

    Args:
        df: A Polars DataFrame with at least a date column and a value column.
        date_col: Name of the date column.
        value_col: Name of the numeric value column.
        fit_window: Number of most-recent data points to use for the fit.
        projection_days: How many days to project into the future.
        title: Optional chart title.
        width: Chart width in pixels, or "container" for responsive. Defaults to "container".
        height: Chart height in pixels (default 400).

    Returns:
        An interactive Altair chart with actual data (solid) and
        forecast (dashed).

    Examples:
        ```python
        import polars as pl
        from wigglystuff import forecast_chart

        df = pl.DataFrame({"date": [...], "value": [...]})
        forecast_chart(df, "date", "value", fit_window=90)
        ```
    """
    import altair as alt
    import numpy as np
    import polars as pl
    from sklearn.linear_model import HuberRegressor

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
        "width": width if width is not None else "container",
        "usermeta": {"embedOptions": {"actions": False}},
    }
    if title:
        props["title"] = title

    chart = (
        (actual_chart + fit_chart)
        .properties(**props)
        .interactive(bind_y=False)
    )
    return chart