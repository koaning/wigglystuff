# SortableList API


 Bases: `AnyWidget`


Drag-and-drop list widget with optional add/remove/edit affordances.



```
from wigglystuff import SortableList

sortable = SortableList(value=["apple", "banana", "cherry"], removable=True)
sortable
```


Create a sortable list widget.


  Source code in `wigglystuff/sortable_list.py`

```
def __init__(
    self,
    value: Sequence[str],
    *,
    addable: bool = False,
    removable: bool = False,
    editable: bool = False,
    label: str = "",
    **kwargs: Any,
) -> None:
    """Create a sortable list widget.

    Args:
        value: Initial sequence of string items.
        addable: Allow inserting new entries.
        removable: Allow deleting entries.
        editable: Enable inline text editing.
        label: Optional heading shown above the list.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    super().__init__(
        value=list(value),
        addable=addable,
        removable=removable,
        editable=editable,
        label=label,
        **kwargs,
    )
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `list[str]` | Ordered list items. |
| `addable` | `bool` | Allow inserting new items. |
| `removable` | `bool` | Allow deleting items. |
| `editable` | `bool` | Allow inline edits. |
| `label` | `str` | Optional heading above the list. |
