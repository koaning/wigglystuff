# DiffViewer API


 Bases: `AnyWidget`


Rich file diff viewer powered by @pierre/diffs.


Displays a side-by-side or unified diff between two file contents, with syntax-aware highlighting and dark mode support.



```
from wigglystuff import DiffViewer

diff = DiffViewer(
    old_name="example.py",
    old_contents="print('hello')",
    new_name="example.py",
    new_contents="print('world')",
)
diff
```


Create a DiffViewer widget.


  Source code in `wigglystuff/diff_viewer.py`

```
def __init__(
    self,
    old_name: str = "",
    old_contents: str = "",
    new_name: str = "",
    new_contents: str = "",
    diff_style: str = "split",
    expand_unchanged: bool = True,
) -> None:
    """Create a DiffViewer widget.

    Args:
        old_name: Filename for the old version.
        old_contents: Text contents of the old version.
        new_name: Filename for the new version.
        new_contents: Text contents of the new version.
        diff_style: Diff display style, either ``"split"`` or ``"unified"``.
        expand_unchanged: Show all unchanged lines instead of collapsing them.
    """
    super().__init__(
        old_name=old_name,
        old_contents=old_contents,
        new_name=new_name,
        new_contents=new_contents,
        diff_style=diff_style,
        expand_unchanged=expand_unchanged,
    )
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `old_name` | `str` | Filename for the old version. |
| `old_contents` | `str` | Text contents of the old version. |
| `new_name` | `str` | Filename for the new version. |
| `new_contents` | `str` | Text contents of the new version. |
| `diff_style` | `str` | `"split"` or `"unified"` (default: `"split"`). |
| `expand_unchanged` | `bool` | Show all unchanged lines instead of collapsing them (default: `True`). |
