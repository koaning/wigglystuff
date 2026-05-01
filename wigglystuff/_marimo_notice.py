"""Internal helper for pointing marimo users at built-in equivalents."""

from __future__ import annotations


_STYLE = (
    "font-size: 0.875em; "
    "padding: 8px 12px; margin: 8px 0; "
    "border-left: 3px solid #f59e0b; "
    "background: rgba(245, 158, 11, 0.10); "
    "border-radius: 0 4px 4px 0;"
)


def warn_if_in_marimo(widget_name: str, message_html: str) -> None:
    """Render a small graduation hint in the cell when running inside marimo.

    No-op in plain Jupyter or non-notebook contexts so users without a
    marimo built-in alternative are not bothered.

    ``message_html`` is treated as raw HTML so call sites can embed
    ``<a href="...">`` links and ``<code>`` tags directly.
    """
    try:
        import marimo as mo
    except ImportError:
        return
    if not mo.running_in_notebook():
        return
    html = (
        f'<div style="{_STYLE}">'
        f"<code>wigglystuff.{widget_name}</code>"
        f" has graduated to marimo core. {message_html}"
        f"</div>"
    )
    mo.output.append(mo.Html(html))
