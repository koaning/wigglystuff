# AnnotationWidget API

::: wigglystuff.annotation.AnnotationWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `action` | `str` | Name of the most recently triggered action (e.g., `accept`, `fail`). |
| `action_timestamp` | `float` | Timestamp (ms since epoch) of the latest action; changes on every trigger so `observe` always fires, even for repeats. |
| `note` | `str` | Free-form note text, populated by typing or speech-to-text. |
| `listening` | `bool` | `True` while speech-to-text is actively transcribing. |
| `disabled` | `bool` | When `True`, all input controls are inert. |
| `show_save` | `bool` | Toggles visibility and availability of the footer Save button. |
| `actions` | `list[str]` | Ordered list of main action button labels. Defaults to `["previous", "accept", "fail", "defer"]`. |
| `keyboard_mapping` | `dict[str, str]` | Maps keys to action names. The special target `mic` toggles the speech-to-text microphone. |
| `gamepad_mapping` | `dict[str, str]` | Maps gamepad button indices (as strings) to action names. The `mic` target works here too. |
| `debounce_ms` | `int` | Minimum interval between accepted action triggers, in milliseconds. |
| `width` | `int` | Widget width in pixels. |
