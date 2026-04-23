"""NestedTable widget -- expandable hierarchy table with per-column values."""

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


Formatter = Callable[[float], str]


class NestedTable(anywidget.AnyWidget):
    """Recursive expandable table for hierarchical data.

    Each row shows the node name followed by one column per value key (or a
    single ``Value`` column when values are scalars), and optionally a
    share-of-root column next to any subset of value columns.

    Args:
        data: Hierarchy dict with leaf values that are either scalars or
            ``{column: number}`` dicts.
        initial_expand_depth: Levels expanded on first render.
        show_percent: Which value columns get a share-of-root column next
            to them. ``True`` (default) enables it for every column,
            ``False`` disables it everywhere, or pass a sequence of column
            names to enable it for just those.
        format: Per-value formatter. Either a callable ``(value) -> str``
            applied to every cell, or a mapping ``{column: callable}`` for
            per-column formatters. Default: integer when whole, else two
            decimals.
        width: CSS width string for the table.

    Examples:
        ```python
        from wigglystuff import NestedTable

        widget = NestedTable.from_paths(
            {
                "analytics/cluster/Agg": {"hours": 12.5, "count": 5},
                "analytics/graph/Shortest": {"hours": 6.0, "count": 2},
                "animate/Easing": {"hours": 4.25, "count": 8},
            },
            format={"hours": lambda v: f"{v:.1f}h"},
            show_percent=["hours"],
        )
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "nested-table.js"

    data = traitlets.Dict(default_value={"name": "root", "children": []}).tag(sync=True)
    columns = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    show_percent = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    initial_expand_depth = traitlets.Int(1).tag(sync=True)
    expanded_paths = traitlets.List(default_value=[]).tag(sync=True)
    selected_path = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    width = traitlets.Unicode("100%").tag(sync=True)

    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        *,
        initial_expand_depth: int = 1,
        show_percent: bool | Sequence[str] = True,
        format: Formatter | Mapping[str, Formatter] | None = None,
        width: str = "100%",
    ):
        prepared, cols = self._prepare(data, formatter=format)
        effective_cols = cols or ["value"]
        if show_percent is True:
            pct_cols = list(effective_cols)
        elif show_percent is False:
            pct_cols = []
        else:
            pct_cols = [c for c in show_percent if c in effective_cols]
            missing = [c for c in show_percent if c not in effective_cols]
            if missing:
                raise ValueError(
                    f"show_percent columns {missing} not found; "
                    f"available: {effective_cols}"
                )
        super().__init__(
            data=prepared,
            columns=cols,
            show_percent=pct_cols,
            initial_expand_depth=initial_expand_depth,
            width=width,
        )

    @staticmethod
    def _prepare(
        data: Mapping[str, Any] | None,
        *,
        formatter: Formatter | Mapping[str, Formatter] | None,
    ) -> tuple[dict, list[str]]:
        if data is None:
            return {"name": "root", "children": []}, []
        tree = copy.deepcopy(dict(data))
        validate_tree(tree)
        aggregate_values(tree)
        cols = collect_columns(tree)
        if formatter is not None:
            _apply_formatter(tree, formatter, cols=cols)
        return tree, cols

    @classmethod
    def from_paths(
        cls,
        mapping: Mapping[str, Any],
        *,
        sep: str = "/",
        root_name: str = "root",
        **kwargs: Any,
    ) -> "NestedTable":
        """Build a ``NestedTable`` from a mapping of path strings to leaf values."""
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
    ) -> "NestedTable":
        """Build a ``NestedTable`` from an iterable of record dicts."""
        tree = tree_from_records(
            records, path_cols=path_cols, value_cols=value_cols, root_name=root_name
        )
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
    ) -> "NestedTable":
        """Build a ``NestedTable`` from a pandas or polars dataframe."""
        tree = tree_from_dataframe(
            df, path_cols=path_cols, value_cols=value_cols, root_name=root_name
        )
        return cls(tree, **kwargs)


def _apply_formatter(
    tree: dict,
    formatter: Formatter | Mapping[str, Formatter],
    *,
    cols: list[str],
) -> None:
    """Walk the tree and bake ``display`` strings into each node."""
    if isinstance(formatter, Mapping):
        per_col: Mapping[str, Formatter] = formatter
        fallback: Formatter | None = None
    else:
        per_col = {}
        fallback = formatter

    def format_value(col: str, value: float) -> str | None:
        fn = per_col.get(col, fallback)
        if fn is None:
            return None
        return fn(value)

    def walk(node: dict) -> None:
        v = node.get("value")
        if isinstance(v, Mapping):
            display: dict[str, str] = {}
            for k, x in v.items():
                out = format_value(k, x)
                if out is not None:
                    display[k] = out
            if display:
                node["display"] = display
        elif v is not None:
            # Scalar: use "value" as the pseudo-column name.
            out = format_value("value", v)
            if out is not None:
                node["display"] = {"value": out}
        for child in node.get("children") or []:
            walk(child)

    walk(tree)
