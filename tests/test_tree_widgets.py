"""Unit tests for Treemap, NestedTable, and the shared tree helpers."""

from __future__ import annotations

import pytest

from wigglystuff import NestedTable, Treemap
from wigglystuff._tree_utils import (
    collect_columns,
    tree_from_dataframe,
    tree_from_paths,
    tree_from_records,
    validate_tree,
)


# ---- tree_from_paths ----


def test_from_paths_scalar():
    tree = tree_from_paths({"a/b": 1, "a/c": 2, "d": 3})
    assert tree["name"] == "root"
    assert {c["name"] for c in tree["children"]} == {"a", "d"}


def test_from_paths_dict_values():
    tree = tree_from_paths({"a/b": {"x": 1.0, "y": 2.0}})
    leaf = tree["children"][0]["children"][0]
    assert leaf["value"] == {"x": 1.0, "y": 2.0}


def test_from_paths_rejects_non_numeric():
    with pytest.raises(ValueError):
        tree_from_paths({"a/b": "not a number"})


def test_from_paths_rejects_dict_with_non_numeric():
    with pytest.raises(ValueError):
        tree_from_paths({"a/b": {"x": "oops"}})


def test_from_paths_duplicate_leaf_raises():
    # "a/b" and "a//b" normalize to the same path tuple.
    with pytest.raises(ValueError, match="duplicate"):
        tree_from_paths({"a/b": 1, "a//b": 2})


# ---- tree_from_records: value_cols ----


RECORDS = [
    {"dept": "eng", "team": "infra", "hours": 40, "tickets": 12, "note": "x"},
    {"dept": "eng", "team": "product", "hours": 70, "tickets": 8, "note": "y"},
    {"dept": "design", "team": "brand", "hours": 55, "tickets": 9, "note": "z"},
]


def test_records_autodetect_value_cols():
    tree = tree_from_records(RECORDS, path_cols=["dept", "team"])
    assert collect_columns(tree) == ["hours", "tickets"]


def test_records_single_string_value_col():
    tree = tree_from_records(RECORDS, path_cols=["dept", "team"], value_cols="hours")
    leaf = tree["children"][0]["children"][0]
    assert isinstance(leaf["value"], (int, float))


def test_records_list_preserves_order():
    tree = tree_from_records(
        RECORDS, path_cols=["dept", "team"], value_cols=["tickets", "hours"]
    )
    assert collect_columns(tree) == ["tickets", "hours"]


def test_records_reject_missing_column():
    with pytest.raises(ValueError, match="bogus"):
        tree_from_records(
            RECORDS, path_cols=["dept", "team"], value_cols=["hours", "bogus"]
        )


def test_records_reject_non_numeric_column():
    with pytest.raises(ValueError, match="note"):
        tree_from_records(
            RECORDS, path_cols=["dept", "team"], value_cols=["hours", "note"]
        )


def test_records_empty_value_cols_list_raises():
    with pytest.raises(ValueError):
        tree_from_records(RECORDS, path_cols=["dept", "team"], value_cols=[])


def test_records_empty_records_raises():
    with pytest.raises(ValueError):
        tree_from_records([], path_cols=["dept"])


def test_records_autodetect_with_only_path_cols_raises():
    with pytest.raises(ValueError, match="no numeric columns"):
        tree_from_records(
            [{"dept": "eng", "team": "infra"}], path_cols=["dept", "team"]
        )


def test_records_empty_path_cols_raises():
    with pytest.raises(ValueError):
        tree_from_records(RECORDS, path_cols=[], value_cols="hours")


# ---- tree_from_dataframe: delegates to records ----


def test_dataframe_polars_roundtrip():
    pl = pytest.importorskip("polars")
    df = pl.DataFrame(
        {
            "dept": ["eng", "eng", "design"],
            "team": ["infra", "product", "brand"],
            "hours": [40, 70, 55],
            "tickets": [12, 8, 9],
        }
    )
    tree = tree_from_dataframe(
        df, path_cols=["dept", "team"], value_cols=["hours", "tickets"]
    )
    assert collect_columns(tree) == ["hours", "tickets"]


def test_dataframe_autodetect():
    pl = pytest.importorskip("polars")
    df = pl.DataFrame(
        {"dept": ["eng"], "team": ["infra"], "hours": [40], "tickets": [12]}
    )
    tree = tree_from_dataframe(df, path_cols=["dept", "team"])
    assert collect_columns(tree) == ["hours", "tickets"]


def test_dataframe_rejects_non_dataframe():
    with pytest.raises(TypeError):
        tree_from_dataframe({"not": "a df"}, path_cols=["x"])


# ---- validate_tree ----


def test_validate_tree_rejects_mixed_modes():
    bad = {
        "name": "root",
        "children": [
            {"name": "a", "value": 1},
            {"name": "b", "value": {"x": 2}},
        ],
    }
    with pytest.raises(ValueError, match="mixes scalar and dict"):
        validate_tree(bad)


def test_validate_tree_requires_string_name():
    with pytest.raises(ValueError):
        validate_tree({"name": 123, "value": 1})


# ---- Treemap widget ----


def test_treemap_basic_scalar():
    widget = Treemap.from_paths({"a/b": 1, "a/c": 2})
    assert widget.data["name"] == "root"


def test_treemap_requires_value_col_for_dict_leaves():
    with pytest.raises(ValueError, match="value_col"):
        Treemap.from_paths({"a/b": {"x": 1, "y": 2}})


def test_treemap_rejects_unknown_value_col():
    with pytest.raises(ValueError, match="bogus"):
        Treemap.from_paths({"a/b": {"x": 1, "y": 2}}, value_col="bogus")


def test_treemap_from_records_autopicks_sizing_dim():
    widget = Treemap.from_records(
        RECORDS, path_cols=["dept", "team"], value_cols=["tickets", "hours"]
    )
    assert widget.value_col == "tickets"


def test_treemap_from_records_respects_explicit_value_col():
    widget = Treemap.from_records(
        RECORDS,
        path_cols=["dept", "team"],
        value_cols=["hours", "tickets"],
        value_col="tickets",
    )
    assert widget.value_col == "tickets"


def test_treemap_format_bakes_display_string():
    widget = Treemap.from_paths(
        {"a/b": {"hours": 1.5}, "a/c": {"hours": 2.25}},
        value_col="hours",
        format=lambda v: f"{v:.1f}h",
    )
    leaf = widget.data["children"][0]["children"][0]
    assert leaf["display"] == "1.5h"


# ---- NestedTable widget ----


def test_nested_table_scalar_columns_empty():
    widget = NestedTable.from_paths({"a/b": 1})
    assert widget.columns == []


def test_nested_table_multi_column_columns_detected():
    widget = NestedTable.from_paths({"a/b": {"hours": 1, "count": 2}})
    assert widget.columns == ["hours", "count"]


def test_nested_table_show_percent_bool_true_expands_all():
    widget = NestedTable.from_paths(
        {"a/b": {"hours": 1, "count": 2}}, show_percent=True
    )
    assert widget.show_percent == ["hours", "count"]


def test_nested_table_show_percent_bool_false_is_empty():
    widget = NestedTable.from_paths(
        {"a/b": {"hours": 1, "count": 2}}, show_percent=False
    )
    assert widget.show_percent == []


def test_nested_table_show_percent_subset():
    widget = NestedTable.from_paths(
        {"a/b": {"hours": 1, "count": 2}}, show_percent=["hours"]
    )
    assert widget.show_percent == ["hours"]


def test_nested_table_show_percent_rejects_unknown_column():
    with pytest.raises(ValueError, match="bogus"):
        NestedTable.from_paths(
            {"a/b": {"hours": 1, "count": 2}}, show_percent=["bogus"]
        )


def test_nested_table_show_percent_scalar_tree():
    widget = NestedTable.from_paths({"a/b": 1}, show_percent=True)
    assert widget.show_percent == ["value"]


def test_nested_table_per_column_formatter_bakes_display():
    widget = NestedTable.from_paths(
        {"a/b": {"hours": 1.5, "count": 3}},
        format={"hours": lambda v: f"{v:.1f}h", "count": lambda v: f"{int(v)} runs"},
    )
    leaf = widget.data["children"][0]["children"][0]
    assert leaf["display"] == {"hours": "1.5h", "count": "3 runs"}


def test_nested_table_no_column_labels_attr():
    # column_labels was removed; constructing with it should fail.
    with pytest.raises(TypeError):
        NestedTable({"name": "r", "children": [{"name": "a", "value": 1}]},
                    column_labels={"value": "x"})
