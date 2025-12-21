# KeystrokeWidget API

## Synced traitlets

`last_key` is a dictionary synced from the browser after each keypress. When no
keypress has been captured yet, it is an empty dict.

| Key | Type | Notes |
| --- | --- | --- |
| `key` | `str` | Display value for the key (e.g., `a`, `Enter`). |
| `code` | `str` | Physical key code (e.g., `KeyA`, `Enter`). |
| `ctrlKey` | `bool` | `True` when Control is held. |
| `shiftKey` | `bool` | `True` when Shift is held. |
| `altKey` | `bool` | `True` when Alt/Option is held. |
| `metaKey` | `bool` | `True` when Command/Meta is held. |
| `timestamp` | `int` | Milliseconds since epoch at capture time. |

::: wigglystuff.keystroke.KeystrokeWidget
