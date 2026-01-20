from wigglystuff import SortableList


def test_basic_initialization():
    """Test that SortableList initializes with expected defaults."""
    widget = SortableList(value=["apple", "banana", "cherry"])
    assert widget.value == ["apple", "banana", "cherry"]
    assert widget.addable is False
    assert widget.removable is False
    assert widget.editable is False
    assert widget.label == ""


def test_sequence_conversion():
    """Test that tuples and other sequences are converted to lists."""
    widget = SortableList(value=("one", "two", "three"))
    assert widget.value == ["one", "two", "three"]
    assert isinstance(widget.value, list)


def test_all_parameters():
    """Test that all constructor parameters work together."""
    widget = SortableList(
        value=["item"],
        addable=True,
        removable=True,
        editable=True,
        label="My List",
    )
    assert widget.value == ["item"]
    assert widget.addable is True
    assert widget.removable is True
    assert widget.editable is True
    assert widget.label == "My List"


def test_value_mutation():
    """Test that value can be modified, simulating frontend reordering."""
    widget = SortableList(value=["first", "second", "third"])
    widget.value = ["third", "first", "second"]
    assert widget.value == ["third", "first", "second"]
