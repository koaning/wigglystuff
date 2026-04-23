"""Treemap widget -- zoomable hierarchical treemap with breadcrumbs."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import anywidget
import traitlets

from ._tree_utils import (
    aggregate_values,
    collect_columns,
    tree_from_dataframe,
    tree_from_paths,
    tree_from_records,
    validate_tree,
)


class Treemap(anywidget.AnyWidget):
    """Zoomable hierarchical treemap.

    Click a rectangle to zoom into its subtree; click the breadcrumb bar
    above the chart to zoom back out. Parent rectangles reserve a header
    strip for their name and aggregated value; children render nested
    inside, up to ``max_depth`` levels below the current view.

    Values on each leaf can be a single number, or a dict of ``{column: number}``
    for multi-column data. In the multi-column case, pass ``value_col`` to pick
    which column drives rectangle sizing.

    Args:
        data: Hierarchy dict.
        width: Chart width. Either an integer in pixels, or a CSS length
            string like ``"100%"`` for responsive sizing.
        height: Chart height in pixels.
        max_depth: How many nesting levels to render below the current
            zoom (default ``3``).
        palette: Optional list of CSS colors. Each top-level group (direct
            child of the root) is painted with a distinct color from the
            palette, and its descendants inherit shaded variants of that
            color. When ``None`` (the default), a balanced built-in palette
            is used. Example: ``palette=["#4e79a7", "#f28e2c", "#e15759",
            "#76b7b2", "#59a14f"]``.
        value_col: When the tree has dict values, the column that drives
            rectangle sizing. Ignored for scalar values.
        format: Optional callable ``(value) -> str`` applied to rectangle
            value labels. Default: raw integer when whole, else two decimals.

    Examples:
        ```python
        from wigglystuff import Treemap

        Treemap.from_paths(
            {
                "analytics/cluster/Agg": {"hours": 10, "count": 5},
                "analytics/graph/Shortest": {"hours": 6, "count": 2},
                "animate/Easing": {"hours": 4, "count": 8},
            },
            value_col="hours",
        )
        ```
    """

    _esm = Path(__file__).parent / "static" / "treemap.js"

    data = traitlets.Dict(default_value={"name": "root", "children": []}).tag(sync=True)
    width = traitlets.Union(
        [traitlets.Int(), traitlets.Unicode()], default_value=600
    ).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    max_depth = traitlets.Int(3).tag(sync=True)
    palette = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    value_col = traitlets.Unicode(default_value="", allow_none=True).tag(sync=True)
    selected_path = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    clicked_path = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)

    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        *,
        width: int | str = 600,
        height: int = 400,
        max_depth: int = 3,
        palette: Sequence[str] | None = None,
        value_col: str | None = None,
        format: Callable[[float], str] | None = None,
    ):
        prepared = self._prepare(data, value_col=value_col, formatter=format)
        super().__init__(
            data=prepared,
            width=width,
            height=height,
            max_depth=max_depth,
            palette=list(palette) if palette else [],
            value_col=value_col or "",
        )

    @staticmethod
    def _prepare(
        data: Mapping[str, Any] | None,
        *,
        value_col: str | None,
        formatter: Callable[[float], str] | None,
    ) -> dict:
        if data is None:
            return {"name": "root", "children": []}
        tree = copy.deepcopy(dict(data))
        validate_tree(tree)
        aggregate_values(tree)
        cols = collect_columns(tree)
        if cols and not value_col:
            raise ValueError(
                f"data has dict values with columns {cols}; pass value_col=... "
                "to pick which column drives rectangle sizing"
            )
        if value_col and cols and value_col not in cols:
            raise ValueError(
                f"value_col={value_col!r} not found; available columns: {cols}"
            )
        if formatter is not None:
            _apply_formatter(tree, formatter, value_col=value_col)
        return tree

    @classmethod
    def from_paths(
        cls,
        mapping: Mapping[str, Any],
        *,
        sep: str = "/",
        root_name: str = "root",
        **kwargs: Any,
    ) -> "Treemap":
        """Build a ``Treemap`` from a mapping of path strings to leaf values."""
        return cls(tree_from_paths(mapping, sep=sep, root_name=root_name), **kwargs)

    @classmethod
    def from_records(
        cls,
        records: Iterable[Mapping[str, Any]],
        *,
        path_cols: Sequence[str],
        value_cols: str | Sequence[str] | None = None,
        root_name: str = "root",
        **kwargs: Any,
    ) -> "Treemap":
        """Build a ``Treemap`` from an iterable of record dicts."""
        tree = tree_from_records(
            records, path_cols=path_cols, value_cols=value_cols, root_name=root_name
        )
        cls._auto_pick_value_col(tree, value_cols, kwargs)
        return cls(tree, **kwargs)

    @classmethod
    def from_dataframe(
        cls,
        df: Any,
        *,
        path_cols: Sequence[str],
        value_cols: str | Sequence[str] | None = None,
        root_name: str = "root",
        **kwargs: Any,
    ) -> "Treemap":
        """Build a ``Treemap`` from a pandas or polars dataframe."""
        tree = tree_from_dataframe(
            df, path_cols=path_cols, value_cols=value_cols, root_name=root_name
        )
        cls._auto_pick_value_col(tree, value_cols, kwargs)
        return cls(tree, **kwargs)

    @staticmethod
    def _auto_pick_value_col(
        tree: dict,
        value_cols: str | Sequence[str] | None,
        kwargs: dict,
    ) -> None:
        if isinstance(value_cols, str):
            return
        if "value_col" in kwargs:
            return
        cols = collect_columns(tree)
        if cols:
            kwargs["value_col"] = cols[0]


def _apply_formatter(
    tree: dict,
    formatter: Callable[[float], str],
    *,
    value_col: str | None,
) -> None:
    """Walk the tree and bake a ``display`` string onto each node for Treemap."""

    def walk(node: dict) -> None:
        v = node.get("value")
        if isinstance(v, Mapping):
            assert value_col is not None
            pick = v.get(value_col)
        else:
            pick = v
        if pick is not None:
            node["display"] = formatter(pick)
        for child in node.get("children") or []:
            walk(child)

    walk(tree)
