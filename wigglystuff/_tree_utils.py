"""Shared helpers for building and validating hierarchical tree dicts.

Both :class:`~wigglystuff.treemap.Treemap` and
:class:`~wigglystuff.nested_table.NestedTable` operate on dicts shaped like
``{"name": str, "value"?: num | dict[str, num], "children"?: [...]}``.

A leaf ``value`` can be either a single number (single-column mode) or a
mapping from column name to number (multi-column mode). Internal nodes may
omit ``value`` -- the widgets sum over their children.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


Tree = dict[str, Any]
Value = float | int | dict[str, float]


def _is_scalar(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_value_dict(v: Any) -> bool:
    if not isinstance(v, Mapping):
        return False
    return all(_is_scalar(x) for x in v.values())


def validate_tree(data: Mapping[str, Any]) -> None:
    """Raise :class:`ValueError` if ``data`` is not a valid tree dict."""
    if not isinstance(data, Mapping):
        raise ValueError(f"tree must be a dict, got {type(data).__name__}")
    mode = {"dict": False, "scalar": False}
    _validate_node(data, path=(), mode=mode)


def _validate_node(node: Mapping[str, Any], path: tuple[str, ...], mode: dict) -> None:
    name = node.get("name")
    if not isinstance(name, str):
        raise ValueError(
            f"node at {list(path) or '<root>'} must have a string 'name', got {name!r}"
        )
    children = node.get("children")
    here = path + (name,)
    if children is None:
        value = node.get("value")
        if _is_scalar(value):
            mode["scalar"] = True
        elif _is_value_dict(value):
            mode["dict"] = True
        else:
            raise ValueError(
                f"leaf node at {list(here)} must have a numeric 'value' "
                f"or a dict of numbers, got {value!r}"
            )
        if mode["scalar"] and mode["dict"]:
            raise ValueError(
                f"tree mixes scalar and dict values (at {list(here)}); "
                "choose one representation"
            )
        return
    if not isinstance(children, list) or not children:
        raise ValueError(
            f"node at {list(here)} has 'children' but it is not a non-empty list"
        )
    for child in children:
        if not isinstance(child, Mapping):
            raise ValueError(
                f"child of {list(here)} must be a dict, got {type(child).__name__}"
            )
        _validate_node(child, here, mode)


def aggregate_values(node: Tree) -> Value:
    """Ensure every node has a ``value``; internal nodes get summed from children.

    Returns the node's resolved value. Mutates the tree in place so all
    downstream consumers see a fully-populated ``value`` on every node.
    Dict values are summed per key (union of child keys).
    """
    children = node.get("children")
    if not children:
        return node["value"]
    aggregated: dict[str, float] | float = {}
    any_dict = False
    any_scalar = False
    for child in children:
        v = aggregate_values(child)
        if isinstance(v, Mapping):
            any_dict = True
            for k, x in v.items():
                aggregated[k] = aggregated.get(k, 0) + x
        else:
            any_scalar = True
            aggregated = (aggregated if isinstance(aggregated, (int, float)) else 0) + v
    if any_dict and any_scalar:
        raise ValueError(
            f"node {node['name']!r} has mixed scalar and dict children"
        )
    if "value" not in node:
        node["value"] = aggregated
    return node["value"]


def collect_columns(node: Tree) -> list[str]:
    """Return dict-value column names (union of all nodes, insertion order)."""
    seen: dict[str, None] = {}

    def walk(n: Tree) -> None:
        v = n.get("value")
        if isinstance(v, Mapping):
            for k in v.keys():
                if k not in seen:
                    seen[k] = None
        for c in n.get("children", []) or []:
            walk(c)

    walk(node)
    return list(seen.keys())


def tree_from_paths(
    mapping: Mapping[str, float | Mapping[str, float]],
    *,
    sep: str = "/",
    root_name: str = "root",
) -> Tree:
    """Build a tree from a mapping of path strings to leaf values.

    Values can be a single number or a ``{col: number}`` dict (multi-column).
    """
    root: Tree = {"name": root_name, "children": []}
    for path, value in mapping.items():
        parts = [p for p in path.split(sep) if p]
        if not parts:
            raise ValueError(f"empty path in mapping (after splitting on {sep!r})")
        _insert_leaf(root, parts, value)
    return root


def tree_from_records(
    records: Iterable[Mapping[str, Any]],
    *,
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None = None,
    root_name: str = "root",
) -> Tree:
    """Build a tree from an iterable of record dicts.

    ``path_cols`` names the hierarchy columns. ``value_cols`` selects
    value columns:

    - ``None`` (default): use every numeric field that isn't in ``path_cols``.
    - ``str``: single-column scalar tree.
    - ``Sequence[str]``: multi-column dict tree, in the given order.

    Raises ``ValueError`` if a requested column is missing or non-numeric,
    or if auto-detection finds no numeric columns.
    """
    if not path_cols:
        raise ValueError("path_cols must be a non-empty sequence")
    records_list = list(records)
    if not records_list:
        raise ValueError("records is empty")
    sample = records_list[0]
    single = isinstance(value_cols, str)
    resolved = _resolve_value_cols(sample, path_cols, value_cols)
    root: Tree = {"name": root_name, "children": []}
    for record in records_list:
        parts = [str(record[col]) for col in path_cols]
        if single:
            value = record[resolved[0]]
        else:
            value = {col: record[col] for col in resolved}
        _insert_leaf(root, parts, value)
    return root


def tree_from_dataframe(
    df: Any,
    *,
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None = None,
    root_name: str = "root",
) -> Tree:
    """Build a tree from a pandas or polars dataframe (duck-typed)."""
    if hasattr(df, "to_dicts"):
        records = df.to_dicts()
    elif hasattr(df, "to_dict"):
        records = df.to_dict(orient="records")
    else:
        raise TypeError(
            f"{type(df).__name__} is not a supported dataframe "
            "(needs .to_dicts() or .to_dict(orient='records'))"
        )
    return tree_from_records(
        records, path_cols=path_cols, value_cols=value_cols, root_name=root_name
    )


def _resolve_value_cols(
    sample: Mapping[str, Any],
    path_cols: Sequence[str],
    value_cols: str | Sequence[str] | None,
) -> list[str]:
    """Return an ordered list of value-column names, validated against sample."""
    if value_cols is None:
        path_set = set(path_cols)
        resolved = [k for k, v in sample.items() if k not in path_set and _is_scalar(v)]
        if not resolved:
            raise ValueError(
                "no numeric columns detected; pass value_cols=... explicitly"
            )
        return resolved
    if isinstance(value_cols, str):
        requested = [value_cols]
    else:
        requested = list(value_cols)
        if not requested:
            raise ValueError("value_cols cannot be empty")
    missing = [c for c in requested if c not in sample]
    if missing:
        raise ValueError(f"value_cols not found in records: {missing}")
    non_numeric = [c for c in requested if not _is_scalar(sample[c])]
    if non_numeric:
        raise ValueError(
            f"value_cols are not numeric: {non_numeric} "
            f"(got {[sample[c] for c in non_numeric]})"
        )
    return requested


def _insert_leaf(root: Tree, parts: list[str], value: Any) -> None:
    if isinstance(value, Mapping):
        if not _is_value_dict(value):
            raise ValueError(f"value at {parts} must be a dict of numbers, got {value!r}")
        coerced: Any = {str(k): float(v) for k, v in value.items()}
    elif _is_scalar(value):
        coerced = value
    else:
        raise ValueError(f"value at {parts} must be numeric, got {value!r}")
    node = root
    for part in parts[:-1]:
        children = node.setdefault("children", [])
        match = next((c for c in children if c.get("name") == part), None)
        if match is None:
            match = {"name": part, "children": []}
            children.append(match)
        elif "children" not in match:
            raise ValueError(f"path {parts} conflicts with existing leaf at {part!r}")
        node = match
    leaf_name = parts[-1]
    siblings = node.setdefault("children", [])
    if any(c.get("name") == leaf_name for c in siblings):
        raise ValueError(f"duplicate leaf at path {parts}")
    siblings.append({"name": leaf_name, "value": coerced})
