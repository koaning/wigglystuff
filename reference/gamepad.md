# GamepadWidget API


 Bases: `AnyWidget`


Listen to browser gamepad events and sync state back to Python.


This widget does not require any initialization arguments; all state is mirrored through traitlets such as `axes` and `current_button_press`.


Examples:


```
gamepad = GamepadWidget()
gamepad
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `current_button_press` | `int` | Index of the most recently pressed button. |
| `current_timestamp` | `float` | Timestamp (ms since epoch) of the latest press. |
| `previous_timestamp` | `float` | Timestamp of the previous press. |
| `axes` | `list[float]` | Analog stick positions (4 values). |
| `dpad_up` | `bool` | D-pad up state. |
| `dpad_down` | `bool` | D-pad down state. |
| `dpad_left` | `bool` | D-pad left state. |
| `dpad_right` | `bool` | D-pad right state. |
| `button_id` | `int` | Reserved for custom mappings (not set by the default UI). |
