# DiffViewer API

::: wigglystuff.diff_viewer.DiffViewer

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `old_name` | `str` | Filename for the old version. |
| `old_contents` | `str` | Text contents of the old version. |
| `new_name` | `str` | Filename for the new version. |
| `new_contents` | `str` | Text contents of the new version. |
| `diff_style` | `str` | `"split"` or `"unified"` (default: `"split"`). |
| `expand_unchanged` | `bool` | Show all unchanged lines instead of collapsing them (default: `True`). |
