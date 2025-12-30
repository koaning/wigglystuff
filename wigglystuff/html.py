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
    display(widget)

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
    display(widget)

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
    the `value` attribute changes. It shows both a graphical representation
    and a numerical indicator (percentage and fraction).

    One of the main benefits of this utility is that you have a progress bar
    that doesn't depend on ipywidgets while you still have something that
    works across notebook projects.

    Attributes:
        value (int): The current progress value. Defaults to 0.
        max_value (int): The maximum value representing 100% completion. Defaults to 100.

    Example:
    
    ```python
    import time
    from wigglystuff import ProgressBar

    progress = ProgressBar(value=0, max_value=100)
    display(progress)

    for i in range(101):
        progress.value = i
        time.sleep(0.1)
    ```
    """

    _esm = """
    function render({ model, el }) {
        let getValue = () => model.get("value");
        let getMaxValue = () => model.get("max_value");

        const container = document.createElement('div');
        container.style.width = '100%';
        container.style.marginBottom = '10px';
        container.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

        // Label
        const label = document.createElement('div');
        label.style.marginBottom = '8px';
        label.style.fontSize = '13px';
        label.style.fontWeight = '500';
        label.style.color = '#666';

        // Progress bar container
        const barContainer = document.createElement('div');
        barContainer.style.width = '100%';
        barContainer.style.height = '24px';
        barContainer.style.borderRadius = '12px';
        barContainer.style.overflow = 'hidden';
        barContainer.style.backgroundColor = '#e0e0e0';
        barContainer.style.border = '1px solid #ccc';
        barContainer.style.boxShadow = 'inset 0 1px 3px rgba(0,0,0,0.1)';

        // Progress fill
        const fill = document.createElement('div');
        fill.style.height = '100%';
        fill.style.transition = 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        fill.style.display = 'flex';
        fill.style.alignItems = 'center';
        fill.style.justifyContent = 'center';
        fill.style.background = 'linear-gradient(90deg, #888 0%, #777 100%)';
        fill.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';

        // Percentage text
        const text = document.createElement('span');
        text.style.fontSize = '11px';
        text.style.fontWeight = '600';
        text.style.color = 'white';
        text.style.textShadow = '0 1px 2px rgba(0,0,0,0.3)';
        text.style.letterSpacing = '0.5px';

        const updateDisplay = () => {
            const value = getValue();
            const max = getMaxValue();
            const percentage = max > 0 ? (value / max) * 100 : 0;

            label.textContent = `Progress: ${value} / ${max}`;
            fill.style.width = percentage + '%';
            text.textContent = Math.round(percentage) + '%';

            // Update text visibility based on bar width
            text.style.opacity = percentage > 10 ? '1' : '0';
        };

        fill.appendChild(text);
        barContainer.appendChild(fill);
        container.appendChild(label);
        container.appendChild(barContainer);

        updateDisplay();

        model.on('change:value', updateDisplay);
        model.on('change:max_value', updateDisplay);

        el.appendChild(container);
    }

    export default { render };
    """

    value = traitlets.Int(0).tag(sync=True)
    max_value = traitlets.Int(100).tag(sync=True)
