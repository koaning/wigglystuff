---
title: "WebkitSpeechToTextWidget: speech to text"
description: WebkitSpeechToTextWidget transcribes what you say into a notebook via the browser's WebKit speech recognition API, syncing the transcript back to Python.
image: speechtotext
image_alt: WebkitSpeechToTextWidget showing a transcribed sentence above a Start Listening button
---

# WebkitSpeechToTextWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="talk" data-demo-title="SpeechToText live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/speechtotext.webp" alt="WebkitSpeechToTextWidget showing a transcribed sentence above a Start Listening button" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`WebkitSpeechToTextWidget` is a thin bridge to the browser's WebKit speech recognition
API: press the button, talk, and the recognized text lands in `transcript` as a Python
string. Setting `trigger_listen` starts a session from code instead of the button, and
`listening` reflects whether recognition is running. Because it delegates to the
browser, availability depends on the browser — WebKit speech recognition is a
Chrome/Safari feature and is absent or unreliable elsewhere, so treat it as
best-effort rather than a dependable transcription pipeline.

See also: [AnnotationWidget](annotation.md) for labelling with speech, keys and buttons
in one surface, [KeystrokeWidget](keystroke.md) for keyboard input, and
[WebcamCapture](webcam-capture.md) for pulling video frames from the same browser APIs.

::: wigglystuff.talk.WebkitSpeechToTextWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `transcript` | `str` | Latest transcript from the browser. |
| `listening` | `bool` | Whether speech recognition is active. |
| `trigger_listen` | `bool` | Toggle listening when set to true (auto-resets). |

