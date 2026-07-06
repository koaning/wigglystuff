# LiveEdit API

::: wigglystuff.live_edit.LiveEdit

::: wigglystuff.live_edit.inspect_run

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Source code for the traced function. This is the future live-edit source of truth. |
| `trace` | `dict` | Structured setup values, loop passes, nested child loops, and returned value. |
| `annotations` | `dict` | Static line/token metadata used by the browser for hover linking. |
| `error` | `dict or None` | Parse, runtime, or argument mismatch error payload; `None` when the run succeeds. |
| `editable` | `bool` | Reserved for the future browser editor mode. Defaults to `False`. |
| `theme` | `str` | `"auto"`, `"light"`, or `"dark"`. |
| `width` | `int` | Widget width in pixels. |
| `height` | `int` | Maximum widget height in pixels. |
