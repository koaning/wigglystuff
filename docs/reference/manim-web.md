# ManimWeb API

::: wigglystuff.manim_web.ManimWeb

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Resolved scene JavaScript (inline JS, or the contents of a file / URL, fetched in Python), run against the manim-web `manim` namespace and a `container` element. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
| `version` | `str` | manim-web version loaded from the CDN. |
| `error` | `str` | Read-back of the latest JS runtime error, or `""`. |
