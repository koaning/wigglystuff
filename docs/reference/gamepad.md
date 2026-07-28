---
title: "GamepadWidget: read gamepad input in Python"
description: GamepadWidget streams the browser Gamepad API into Python traitlets, mirroring analog stick axes, D-pad state and the most recent button press in marimo.
image: gamepad
image_alt: GamepadWidget showing a connected 8BitDo controller with the current button press, D-pad and stick positions
---

# GamepadWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="gamepad" data-demo-title="GamepadWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/gamepad.webp" alt="GamepadWidget showing a connected 8BitDo controller with the current button press, D-pad and stick positions" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`GamepadWidget` polls the browser's Gamepad API and mirrors the controller state into
traitlets: `axes` for the two analog sticks, four booleans for the D-pad, and
`current_button_press` plus timestamps for the latest button. It takes no arguments —
plug in a controller, press a button so the browser reports it, and observe the traits.
Useful for labelling loops and robot teleop where a keyboard is the wrong shape.

See also: [KeystrokeWidget](keystroke.md) for keyboard shortcuts instead of a controller,
[AnnotationWidget](annotation.md) for a labelling surface that already maps buttons,
keys and a gamepad to actions, and [WebkitSpeechToTextWidget](talk.md) for voice input.

::: wigglystuff.gamepad.GamepadWidget

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

