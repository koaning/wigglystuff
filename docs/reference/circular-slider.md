# CircularSlider API

::: wigglystuff.circular_slider.CircularSlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `float` | Current value, mapped onto the circular track. |
| `start` | `float` | Lower bound of the value range (sits at 12 o'clock). |
| `stop` | `float` | Upper bound of the value range. |
| `step` | `float` | Snap increment in value units. |
| `size` | `int` | Diameter in pixels. |
| `thickness` | `int` | Ring track thickness in pixels. |
| `show_value` | `bool` | Render the current value as text below the dial. |
| `color` | `str` | CSS color for the fill arc and handle border (e.g. `"#ef4444"`). Empty string follows the light/dark theme. |
| `label` | `str` | Optional text label shown above the dial. Empty string hides it. |

---

::: wigglystuff.circular_slider.CircularRangeSlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `tuple[float, float]` | Current `(low, high)` range. A drag that crosses the 12 o'clock seam produces a wrap-around tuple where `low > high`. |
| `start` | `float` | Lower bound of the value range. |
| `stop` | `float` | Upper bound of the value range. |
| `step` | `float` | Snap increment in value units. |
| `size` | `int` | Diameter in pixels. |
| `thickness` | `int` | Ring track thickness in pixels. |
| `show_value` | `bool` | Render the current `low – high` range as text below the dial. |
