"""DiffViewer widget for rendering file diffs with split or unified views."""

from pathlib import Path
from typing import Any

import anywidget
import traitlets


class DiffViewer(anywidget.AnyWidget):
    """Rich file diff viewer powered by @pierre/diffs.

    Displays a side-by-side or unified diff between two file contents,
    with syntax-aware highlighting and dark mode support.

    Examples:
        ```python
        diff = DiffViewer(
            old_name="example.py",
            old_contents="print('hello')",
            new_name="example.py",
            new_contents="print('world')",
        )
        diff
        ```
    """

    _esm = Path(__file__).parent / "static" / "diff-viewer.js"

    old_name = traitlets.Unicode("").tag(sync=True)
    old_contents = traitlets.Unicode("").tag(sync=True)
    new_name = traitlets.Unicode("").tag(sync=True)
    new_contents = traitlets.Unicode("").tag(sync=True)
    diff_style = traitlets.Unicode("split").tag(sync=True)
    expand_unchanged = traitlets.Bool(True).tag(sync=True)

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

    @traitlets.validate("diff_style")
    def _validate_diff_style(self, proposal: dict[str, Any]) -> str:
        """Ensure diff_style is 'split' or 'unified'."""
        value = proposal["value"]
        if value not in ("split", "unified"):
            raise traitlets.TraitError("diff_style must be 'split' or 'unified'.")
        return value
