"""ObservablePlot widget for running Observable Plot code in the notebook."""

from pathlib import Path
from typing import Any, Dict, Optional

import anywidget
import traitlets


class ObservablePlot(anywidget.AnyWidget):
    """Run `Observable Plot <https://observablehq.com/plot/>`_ code in a notebook.

    Observable Plot is a JavaScript charting library. This widget is a thin
    runner: it loads Plot (and d3) from a CDN, then evaluates a blob of
    JavaScript you supply (the ``code`` traitlet) exactly as you would write it
    in an Observable notebook — a bare ``Plot.plot({...})`` expression that
    returns a DOM node. The returned node is mounted inline; Python's job is to
    hand over the source, the data, and the sizing.

    Python values are injected into the code's scope by name via ``variables``:
    each key becomes an in-scope JavaScript variable holding the (JSON-ified)
    value. So ``variables={"vacancies": df}`` lets your code reference
    ``vacancies`` directly::

        Plot.plot({
            marks: [
                Plot.barY(vacancies, { x: "month", y: "vacancies" }),
                Plot.ruleY([0]),
            ],
        })

    ``Plot`` and ``d3`` are always in scope, along with ``container`` (the
    target DOM element), the ``width`` / ``height`` ints, and the widget
    ``model``. Pandas / polars DataFrames and numpy arrays in ``variables`` are
    converted to plain JSON structures (records / lists) before syncing.

    The code is evaluated verbatim in the browser, so only pass JavaScript you
    trust (typically your own).

    Reassigning ``code``, ``variables``, ``width``, ``height``, or ``version``
    re-runs the code and rebuilds the chart. Observable Plot has no incremental
    redraw — each run produces a fresh SVG — but the new node is swapped in
    atomically (the previous chart stays put until it is ready), so updates
    driven by e.g. a slider do not flash a blank frame.

    Examples:
        ```python
        import marimo as mo
        import pandas as pd
        from wigglystuff import ObservablePlot

        df = pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "vacancies": [3, 5, 2]})
        code = '''
            Plot.plot({
                marks: [
                    Plot.barY(vacancies, { x: "month", y: "vacancies" }),
                    Plot.ruleY([0]),
                ],
            })
        '''
        mo.ui.anywidget(ObservablePlot(code, variables={"vacancies": df}))
        ```

        Point at a local file or a URL instead of an inline string — the first
        argument accepts any of the three forms:

        ```python
        ObservablePlot("charts/bars.js", variables={"vacancies": df})
        ObservablePlot("https://example.com/chart.js")
        ```
    """

    _esm = Path(__file__).parent / "static" / "observable-plot.js"
    _css = Path(__file__).parent / "static" / "observable-plot.css"

    code = traitlets.Unicode("").tag(sync=True)
    variables = traitlets.Dict({}).tag(sync=True)
    width = traitlets.Int(500).tag(sync=True)
    height = traitlets.Int(300).tag(sync=True)
    version = traitlets.Unicode("latest").tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        code: Optional[str] = None,
        *,
        src: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        width: int = 500,
        height: int = 300,
        version: str = "latest",
        **kwargs: Any,
    ) -> None:
        """Create an ObservablePlot widget.

        The plot source is resolved in Python, so the browser always receives
        plain JavaScript. ``code`` (or ``src``) may be any of:

        * an inline JavaScript string,
        * a path to a local ``.js`` file, or
        * an ``http(s)://`` URL.

        URLs and file paths are fetched/read here at construction time; the
        detection is by value, so ``ObservablePlot("https://.../chart.js")`` and
        ``ObservablePlot("Plot.plot({...})")`` both do the right thing.

        Args:
            code: Inline JavaScript, a local file path, or an ``http(s)://``
                URL. Mutually exclusive with ``src``.
            src: An explicit alias for ``code`` (same accepted forms), handy
                when the intent is "load from here". Mutually exclusive with
                ``code``.
            variables: Mapping of name -> value injected into the code's scope
                as JavaScript variables. DataFrames and numpy arrays are
                converted to JSON-serializable structures.
            width: Container width in pixels.
            height: Container height in pixels.
            version: The `@observablehq/plot` version to load from the CDN.
                Defaults to ``"latest"``; pin an exact version (e.g. ``"0.6.17"``)
                for reproducibility.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.

        Raises:
            ValueError: If neither or both of ``code`` and ``src`` are given.
        """
        if (code is None) == (src is None):
            raise ValueError("Provide exactly one of `code` or `src`.")

        source = code if code is not None else src
        super().__init__(
            code=self._resolve_source(source),
            variables=variables if variables is not None else {},
            width=width,
            height=height,
            version=version,
            **kwargs,
        )

    @traitlets.validate("variables")
    def _validate_variables(self, proposal: Any) -> Dict[str, Any]:
        # Convert on every assignment, so `widget.variables = {"df": df}` works
        # the same as passing it to the constructor.
        return self._convert_variables(proposal["value"])

    @staticmethod
    def _resolve_source(source: str) -> str:
        """Return plot JS: fetch a URL, read a local file, or pass JS through."""
        text = str(source)
        if text.startswith("http://") or text.startswith("https://"):
            import urllib.request

            with urllib.request.urlopen(text) as response:
                return response.read().decode("utf-8")
        # A path to an existing file? Read it. Otherwise treat it as inline JS.
        # (Multi-line JS makes an invalid path, so is_file() is safely False.)
        try:
            path = Path(text)
            if path.is_file():
                return path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            pass
        return text

    @classmethod
    def _convert_variables(
        cls, variables: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert each injected variable to a JSON-serializable form."""
        if variables is None:
            return {}
        if not isinstance(variables, dict):
            raise TypeError("`variables` must be a dict of name -> value.")
        return {str(name): cls._to_jsonable(value) for name, value in variables.items()}

    @staticmethod
    def _to_jsonable(value: Any) -> Any:
        """Coerce DataFrames / numpy types to plain JSON-serializable values.

        Duck-typed so pandas, polars, and numpy stay optional dependencies.
        Anything already JSON-native (lists, dicts, str, numbers, bool, None)
        passes straight through.
        """
        # polars DataFrame (check first -- polars also has .to_dict)
        if hasattr(value, "to_dicts") and callable(value.to_dicts):
            return value.to_dicts()
        # pandas DataFrame
        if hasattr(value, "to_dict") and callable(value.to_dict):
            return value.to_dict("records")
        # numpy array (or anything array-like exposing tolist)
        if hasattr(value, "tolist") and callable(value.tolist):
            return value.tolist()
        # numpy scalar -> Python native
        if hasattr(value, "item") and callable(value.item):
            return value.item()
        return value
