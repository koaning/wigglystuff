import base64
import io
from pathlib import Path
from tempfile import TemporaryDirectory

import anywidget
import traitlets


class ImageRefreshWidget(anywidget.AnyWidget):
    """A widget that displays an image and refreshes when the source changes.

    This widget creates an image element that automatically updates whenever
    the `src` attribute is modified, making it ideal for displaying dynamically
    generated images in Jupyter notebooks.

    Attributes:
        src (str): The image source, typically a base64-encoded data URI.

    Example:

    ```python
    from wigglystuff import ImageRefreshWidget
    from wigglystuff.utils import refresh_matplotlib
    import matplotlib.pylab as plt
    import numpy as np

    @refresh_matplotlib
    def plot_data(data):
        plt.plot(np.arange(len(data)), np.cumsum(data))

    widget = ImageRefreshWidget(src=plot_data([1, 2, 3, 4]))

    # Update the widget with new data
    widget.src = plot_data([1, 2, 3, 4, 5, 6])
    ```
    """

    _esm = """
    function render({ model, el }) {
      let src = () => model.get("src");
      let image = document.createElement("img");
      image.src = src();
      model.on("change:src", () => {
        image.src = src();
      });
      el.appendChild(image);
    }
    export default { render };
    """
    src = traitlets.Unicode().tag(sync=True)



class HTMLRefreshWidget(anywidget.AnyWidget):
    """A widget that displays HTML content and refreshes when it changes.

    This widget creates a div element that automatically updates whenever
    the `html` attribute is modified, making it ideal for displaying dynamically
    generated HTML content like SVG charts in Jupyter notebooks.

    Attributes:
        html (str): The HTML content to display.

    Example:

    ```python
    import time
    from wigglystuff import HTMLRefreshWidget

    widget = HTMLRefreshWidget(html="<p>Hello!</p>")

    # Update the widget with dynamic content
    for i in range(10):
        widget.html = f"<p>Count: {i}</p>"
        time.sleep(0.5)
    ```
    """

    _esm = """
    function render({ model, el }) {
      let elem = () => model.get("html");
      let div = document.createElement("div");
      div.innerHTML = elem();
      model.on("change:html", () => {
        div.innerHTML = elem();
      });
      el.appendChild(div);
    }
    export default { render };
    """
    html = traitlets.Unicode().tag(sync=True)



class ProgressBar(anywidget.AnyWidget):
    """A customizable progress bar widget for notebooks.

    This widget displays a visual progress bar that updates in real-time as
    the `value` attribute changes.

    One of the main benefits of this utility is that you have a progress bar
    that doesn't depend on ipywidgets while you still have something that
    works across notebook projects.

    Attributes:
        value (int): The current progress value. Defaults to 0.
        max_value (int): The maximum value representing 100% completion. Defaults to 100.
        color (str): The fill color of the progress bar. Defaults to '#22c55e'.
        show_text (bool): Whether to show the progress text below the bar. Defaults to True.
        width (str): The CSS width of the progress bar. Defaults to '100%'.
        height (int): The height of the bar in pixels. Defaults to 24.

    Example:

    ```python
    import time
    from wigglystuff import ProgressBar

    progress = ProgressBar(value=0, max_value=100)

    for i in range(101):
        progress.value = i
        time.sleep(0.1)
    ```
    """

    _esm = """
    function render({ model, el }) {
        const wrapper = document.createElement('div');
        wrapper.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

        const bar = document.createElement('div');
        bar.style.borderRadius = '4px';
        bar.style.overflow = 'hidden';
        bar.style.backgroundColor = '#374151';

        const fill = document.createElement('div');
        fill.style.height = '100%';
        fill.style.transition = 'width 0.4s ease';

        const text = document.createElement('div');
        text.style.fontSize = '12px';
        text.style.fontWeight = '500';
        text.style.color = '#888';
        text.style.marginTop = '4px';
        text.style.textAlign = 'center';

        bar.appendChild(fill);
        wrapper.appendChild(bar);
        wrapper.appendChild(text);

        const updateDisplay = () => {
            const value = model.get("value");
            const max = model.get("max_value");
            const percentage = max > 0 ? (value / max) * 100 : 0;

            wrapper.style.width = model.get("width");
            bar.style.height = model.get("height") + 'px';
            fill.style.backgroundColor = model.get("color");
            fill.style.width = percentage + '%';

            const showText = model.get("show_text");
            text.style.display = showText ? 'block' : 'none';
            text.textContent = `${value} / ${max}`;
        };

        updateDisplay();

        model.on('change:value', updateDisplay);
        model.on('change:max_value', updateDisplay);
        model.on('change:color', updateDisplay);
        model.on('change:show_text', updateDisplay);
        model.on('change:width', updateDisplay);
        model.on('change:height', updateDisplay);

        el.appendChild(wrapper);
    }

    export default { render };
    """

    value = traitlets.Int(0).tag(sync=True)
    max_value = traitlets.Int(100).tag(sync=True)
    color = traitlets.Unicode('#22c55e').tag(sync=True)
    show_text = traitlets.Bool(True).tag(sync=True)
    width = traitlets.Unicode('100%').tag(sync=True)
    height = traitlets.Int(24).tag(sync=True)
