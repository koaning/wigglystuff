# Simple Build Guide: One Widget at a Time

## Overview

We build widgets one at a time using esbuild. Simple and straightforward!

## How It Works

### React/TypeScript Widgets

Use relative imports to access shared components:

```tsx
// js/paint/widget.tsx
import { Button } from '../shared/components/Button';

function Component() {
  return <Button variant="primary">Click me</Button>;
}
```

Build with:
```bash
make js-paint
```

The Makefile handles:
- JSX compilation (`--jsx=automatic`)
- Externalizing React (provided by `@anywidget/react`)
- Bundling shared components into the widget
- Tailwind CSS compilation (if needed)

### Vanilla JavaScript Widgets

No changes needed - they work as-is:

```bash
make js-talk
```

## Updated Makefile Targets

### React Widgets (with shared component support)

```makefile
js-copybutton:
	./node_modules/.bin/esbuild js/copybutton/widget.tsx \
		--bundle --format=esm \
		--jsx=automatic \
		--external:react --external:react-dom \
		--outfile=wigglystuff/static/copybutton.js

js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		--bundle --format=esm \
		--jsx=automatic \
		--external:react --external:react-dom \
		--outfile=wigglystuff/static/paint.js \
		--minify
```

### Vanilla JS Widgets (unchanged)

```makefile
js-talk:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/talk-widget.js js/talk/widget.js
```

## Using Shared Components

### 1. Create Shared Component

```tsx
// js/shared/components/Button.tsx
import * as ButtonPrimitive from "@radix-ui/react-button";
import * as React from "react";

export interface ButtonProps extends React.ComponentPropsWithoutRef<typeof ButtonPrimitive.Root> {
  variant?: 'default' | 'primary' | 'secondary';
}

export const Button = React.forwardRef<
  React.ElementRef<typeof ButtonPrimitive.Root>,
  ButtonProps
>(({ variant = 'default', ...props }, ref) => {
  return <ButtonPrimitive.Root ref={ref} {...props} />;
});
```

### 2. Export from Index

```tsx
// js/shared/components/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button';
```

### 3. Use in Widget

```tsx
// js/paint/widget.tsx
import { Button } from '../shared/components/Button';

function Component() {
  return <Button variant="primary">Click me</Button>;
}
```

### 4. Build

```bash
make js-paint
```

esbuild automatically:
- Resolves the relative import
- Bundles the Button component
- Includes Radix UI dependencies
- Outputs a single bundled file

## CSS for Vanilla JS Widgets

If you create shared CSS for vanilla JS widgets:

```makefile
# Copy shared Radix CSS
js-shared-css:
	cp js/shared/styles/button.css wigglystuff/static/radix-button.css
```

Then include in your Python widget:

```python
widget = anywidget.AnyWidget(
    _esm=pathlib.Path(__file__).parent / "static" / "my-widget.js",
    _css=pathlib.Path(__file__).parent / "static" / "radix-button.css",
)
```

## Watch Mode (Optional)

For development, you can add watch targets:

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

## Key Points

✅ **Relative imports** - No aliases needed, esbuild handles it  
✅ **One widget at a time** - Build exactly what you need  
✅ **Simple Makefile** - Just add `--jsx=automatic` for React widgets  
✅ **Shared components bundled** - Automatically included in widget bundle  
✅ **No config files** - Everything in Makefile  

## Example: Migrating Copy Button to Use Shared Button

1. **Create shared Button component** (see above)

2. **Update copybutton widget:**
   ```tsx
   // js/copybutton/widget.tsx
   import { Button } from '../shared/components/Button';
   import { CopyIcon } from '@radix-ui/react-icons';
   
   function CopyToClipboardButton() {
     return (
       <Button onClick={() => copyToClipboard(text_to_copy)}>
         <CopyIcon /> Copy to Clipboard
       </Button>
     );
   }
   ```

3. **Build:**
   ```bash
   make js-copybutton
   ```

Done! The shared Button component is now bundled into the copybutton widget.
