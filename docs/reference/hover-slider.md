# HoverSlider API

::: wigglystuff.hover_slider.HoverSlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int \| float` | Committed value. Moves on click, drag, and arrow keys — never on plain hover. |
| `hover_value` | `int \| float` | Value under the pointer. Falls back to `value` when the pointer leaves, so it is never `None`. |
| `hovering` | `bool` | Whether the pointer is on the track, i.e. whether `hover_value` is live. |
| `start` | `int \| float` | Lower bound. In `steps` mode this is `steps[0]`. |
| `stop` | `int \| float` | Upper bound. In `steps` mode this is `steps[-1]`. |
| `step` | `int \| float \| None` | Snap increment. `None` in `steps` mode. |
| `steps` | `list[int \| float]` | Discrete values, laid out evenly across the track. Empty means linear mode. |
| `sync_throttle_ms` | `int` | Cap on how often hover updates reach Python. `0` syncs every pointer move. |
| `show_value` | `bool` | Render the committed and hovered values below the track. |
| `label` | `str` | Text above the track. Empty string hides it. |
| `color` | `str` | CSS color for the fill, puck border, and hover marker. Empty uses the theme default. |
| `width` | `int` | Widget width in pixels. |
