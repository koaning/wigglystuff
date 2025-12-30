import base64
import io 
from pathlib import Path
from tempfile import TemporaryDirectory


def altair2svg(chart):
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

def refresh_matplotlib(func):
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


def refresh_altair(func):
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