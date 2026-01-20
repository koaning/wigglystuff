import pytest

from wigglystuff import SortableList


def test_basic_initialization():
    widget = SortableList(value=["apple", "banana", "cherry"])
    assert widget.value == ["apple", "banana", "cherry"]


def test_tuple_input_converted_to_list():
    widget = SortableList(value=("one", "two", "three"))
    assert widget.value == ["one", "two", "three"]
    assert isinstance(widget.value, list)


def test_generator_input_converted_to_list():
    def gen():
        yield "a"
        yield "b"
        yield "c"

    widget = SortableList(value=gen())
    assert widget.value == ["a", "b", "c"]


def test_empty_list():
    widget = SortableList(value=[])
    assert widget.value == []


def test_default_flags_are_false():
    widget = SortableList(value=["item"])
    assert widget.addable is False
    assert widget.removable is False
    assert widget.editable is False


def test_default_label_is_empty():
    widget = SortableList(value=["item"])
    assert widget.label == ""


def test_addable_flag():
    widget = SortableList(value=["item"], addable=True)
    assert widget.addable is True
    assert widget.removable is False
    assert widget.editable is False


def test_removable_flag():
    widget = SortableList(value=["item"], removable=True)
    assert widget.addable is False
    assert widget.removable is True
    assert widget.editable is False


def test_editable_flag():
    widget = SortableList(value=["item"], editable=True)
    assert widget.addable is False
    assert widget.removable is False
    assert widget.editable is True


def test_all_flags_enabled():
    widget = SortableList(
        value=["item"],
        addable=True,
        removable=True,
        editable=True,
    )
    assert widget.addable is True
    assert widget.removable is True
    assert widget.editable is True


def test_label_set():
    widget = SortableList(value=["item"], label="My List")
    assert widget.label == "My List"


def test_value_can_be_modified():
    widget = SortableList(value=["a", "b"])
    widget.value = ["c", "d", "e"]
    assert widget.value == ["c", "d", "e"]


def test_reorder_simulation():
    """Simulates what happens when the frontend reorders items."""
    widget = SortableList(value=["first", "second", "third"])
    # Frontend would send back reordered list
    widget.value = ["third", "first", "second"]
    assert widget.value == ["third", "first", "second"]
