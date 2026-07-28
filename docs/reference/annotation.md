---
title: "AnnotationWidget: label data in notebooks"
description: AnnotationWidget is an annotation surface with action buttons, keyboard shortcuts, gamepad input and speech-to-text notes for labeling runs in marimo.
image: annotation
image_alt: AnnotationWidget showing previous, accept, fail and defer buttons above a note field with a microphone
---

# AnnotationWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="annotation" data-demo-title="AnnotationWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/annotation.webp" alt="AnnotationWidget showing previous, accept, fail and defer buttons above a note field with a microphone" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`AnnotationWidget` is the input half of an annotation workflow: a row of action buttons
(`previous`, `accept`, `fail`, `defer` by default), a note field with speech-to-text, and
the same actions bound to number keys and gamepad buttons so you can label a queue
without reaching for the mouse. It deliberately does not render the thing being
annotated — your notebook shows the content and reacts to the `action` traitlet, and
because `action_timestamp` changes on every trigger, `observe` fires even when the same
action is picked twice in a row.

See also: [KeystrokeWidget](keystroke.md) for raw keypresses without the button UI,
[GamepadWidget](gamepad.md) for reading a controller's axes and buttons directly, and
[ProgressBar](progress-bar.md) for showing how far through the queue you are.

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
| `keyboard_mapping` | `dict[str, str]` | Maps keys to action names. By default, action buttons are mapped to number keys in order (`1`, `2`, ...), with `s` for save and `m` for mic. The special target `mic` toggles the speech-to-text microphone. |
| `gamepad_mapping` | `dict[str, str]` | Maps gamepad button indices (as strings) to action names. By default, action buttons are mapped to gamepad buttons in order (`0`, `1`, ...), followed by save and mic. The `mic` target works here too. |
| `debounce_ms` | `int` | Minimum interval between accepted action triggers, in milliseconds. |
| `width` | `int` | Widget width in pixels. |
