# Simple Build Approach: One Widget at a Time

Since we only build one widget at a time, we can keep using esbuild directly with minimal changes.

## Solution: Relative Imports + Updated Makefile

### 1. Use Relative Imports for Shared Components

Instead of `@shared`, use relative paths:

```tsx
// js/paint/widget.tsx
import { Button } from '../shared/components/Button';

// js/copybutton/widget.tsx
import { Button } from '../shared/components/Button';
```

No alias needed! esbuild handles relative imports automatically.

### 2. Update Makefile for React Widgets

Just add `--jsx=automatic` and `--external:react` for React widgets:

```makefile
# React/TypeScript widgets
js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		--bundle --format=esm \
		--jsx=automatic \
		--external:react --external:react-dom \
		--outfile=wigglystuff/static/paint.js \
		--minify

js-copybutton:
	./node_modules/.bin/esbuild js/copybutton/widget.tsx \
		--bundle --format=esm \
		--jsx=automatic \
		--external:react --external:react-dom \
		--outfile=wigglystuff/static/copybutton.js \
		--minify

# Vanilla JS widgets (no changes needed)
js-talk:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/talk-widget.js js/talk/widget.js
```

### 3. Watch Mode (Optional)

Add watch targets if needed:

```makefile
js-paint-watch:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css --watch &
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		--bundle --format=esm \
		--jsx=automatic \
		--external:react --external:react-dom \
		--outfile=wigglystuff/static/paint.js \
		--watch
```

## That's It!

- ✅ No complex build scripts
- ✅ No configuration files
- ✅ Just update Makefile targets
- ✅ Use relative imports for shared components
- ✅ esbuild handles everything

## Example: Using Shared Button Component

1. **Create shared component:**
   ```tsx
   // js/shared/components/Button.tsx
   import * as ButtonPrimitive from "@radix-ui/react-button";
   
   export function Button(props) {
     return <ButtonPrimitive.Root {...props} />;
   }
   ```

2. **Use in widget:**
   ```tsx
   // js/paint/widget.tsx
   import { Button } from '../shared/components/Button';
   
   function Component() {
     return <Button>Click me</Button>;
   }
   ```

3. **Build:**
   ```bash
   make js-paint
   ```

esbuild automatically bundles the Button component into the widget!

## CSS for Shared Components

For vanilla JS widgets that need Radix CSS:

1. **Create CSS file:**
   ```css
   /* js/shared/styles/button.css */
   .radix-button { ... }
   ```

2. **Copy in Makefile:**
   ```makefile
   js-shared-css:
   	cp js/shared/styles/button.css wigglystuff/static/radix-button.css
   ```

3. **Include in Python widget:**
   ```python
   widget = anywidget.AnyWidget(
       _esm=pathlib.Path(__file__).parent / "static" / "my-widget.js",
       _css=pathlib.Path(__file__).parent / "static" / "radix-button.css",
   )
   ```

## Benefits

- ✅ **Simple** - No new tools or scripts
- ✅ **Familiar** - Same Makefile approach
- ✅ **Flexible** - Each widget builds independently
- ✅ **Fast** - esbuild is already fast
- ✅ **Works now** - Just update Makefile targets

No need for the complex build script - esbuild handles everything!
