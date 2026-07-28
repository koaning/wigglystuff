---
title: "CopyToClipboard: copy text button widget"
description: CopyToClipboard renders a button that writes any Python string to the OS clipboard, handy for passing prompts, tokens or SQL out of a Colab notebook.
image: copytoclipboard
image_alt: CopyToClipboard widget rendered as a small grey button labeled Copy to Clipboard with a copy icon
---

# CopyToClipboard API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="copytoclipboard" data-demo-title="CopyToClipboard live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/copytoclipboard.webp" alt="CopyToClipboard widget rendered as a small grey button labeled Copy to Clipboard with a copy icon" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`CopyToClipboard` is a single button that writes `text_to_copy` to the OS clipboard when
clicked. Because `text_to_copy` is a synced traitlet, you can keep setting it from Python
and the button always carries the current value — useful for a generated prompt, a
connection string, or a block of SQL that the reader needs to paste somewhere else.

See also: [ColorPicker](color-picker.md) for producing a hex string worth copying,
[AnnotationWidget](annotation.md) for capturing text the other direction, and
[HTMLRefreshWidget](html-refresh.md) for showing that text in the cell instead.

::: wigglystuff.copy_to_clipboard.CopyToClipboard

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `text_to_copy` | `str` | Payload copied when the button is pressed. |

