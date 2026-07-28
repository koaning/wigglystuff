---
title: "KeystrokeWidget: capture keyboard shortcuts"
description: KeystrokeWidget captures the latest keypress with its modifier keys and reports key, code and timestamp to Python so a notebook can react to shortcuts.
image: keystroke
image_alt: KeystrokeWidget showing a captured Meta plus K shortcut with its key code and timestamp
---

# KeystrokeWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="keystroke" data-demo-title="KeystrokeWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/keystroke.webp" alt="KeystrokeWidget showing a captured Meta plus K shortcut with its key code and timestamp" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`KeystrokeWidget` records the most recent keypress made while the widget has focus and
puts it in `last_key` as a dict mirroring the browser `KeyboardEvent`: `key`, `code`, the
four modifier booleans, and a millisecond `timestamp`. It takes no arguments. Click the
panel first, then press a combination — the timestamp changes on every press, so
observing `last_key` also catches the same shortcut being hit twice in a row.

See also: [GamepadWidget](gamepad.md) for controller buttons and sticks,
[AnnotationWidget](annotation.md) for mapping keys straight onto labelling actions, and
[WebkitSpeechToTextWidget](talk.md) for dictating instead of typing.

::: wigglystuff.keystroke.KeystrokeWidget

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

