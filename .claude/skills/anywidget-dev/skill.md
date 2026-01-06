# anywidget Development

Build an anywidget component with vanilla JavaScript and proper styling.

## Instructions

When creating an anywidget:

1. **Use vanilla JavaScript in `_esm`**:
   - Define a `render` function that takes `{ model, el }` as parameters
   - Use `model.get()` to read trait values
   - Use `model.set()` and `model.save_changes()` to update traits
   - Listen to changes with `model.on("change:traitname", callback)`
   - Export default with `export default { render };` at the bottom

2. **Include `_css` styling**:
   - Keep CSS minimal unless explicitly asked for more
   - Make it look bespoke in both light and dark mode
   - Use CSS media query for dark mode: `@media (prefers-color-scheme: dark) { ... }`

3. **Wrap the widget for display**:
   - Always wrap with marimo: `widget = mo.ui.anywidget(OriginalAnywidget())`
   - Access values via `widget.value` which returns a dictionary

4. **Keep examples minimal**:
   - Show basic usage only
   - Don't combine with other marimo UI elements unless explicitly requested

## Example Structure

```python
import anywidget
import traitlets

class MyWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      // Your vanilla JavaScript here
      let value = model.get("trait_name");

      // Create elements
      let container = document.createElement("div");

      // Listen to changes
      model.on("change:trait_name", () => {
        // Update UI
      });

      el.appendChild(container);
    }
    export default { render };
    """

    _css = """
    /* Light mode styles */
    .container {
      /* styles */
    }

    /* Dark mode styles */
    @media (prefers-color-scheme: dark) {
      .container {
        /* dark mode styles */
      }
    }
    """

    trait_name = traitlets.Unicode("default").tag(sync=True)

# Wrap with marimo
widget = mo.ui.anywidget(MyWidget())
widget
```

## Accessing Values

```python
# In another cell
widget.value["trait_name"]
```
