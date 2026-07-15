# EsmWidget API

::: wigglystuff.esm_widget.EsmWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Resolved ES module JavaScript (inline JS, or the contents of a file / URL, fetched in Python). Must `export default { render }`; loaded in the browser as a real module, so top-level `import` statements work. |
| `css` | `str` | Optional inline CSS injected into the widget root. |
| `data` | `Any` | Any JSON-able value, synced two-way. Changing it fires `change:data` in the browser but does **not** re-run `render`. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
| `error` | `str` | Read-back of the latest JS runtime error, or `""`. |
