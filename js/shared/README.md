# Shared Components Directory

This directory contains shared React components, CSS, and utilities that can be used across multiple widgets.

## Structure

```
js/shared/
├── components/          # React components (Button, Input, etc.)
│   ├── Button.tsx
│   ├── index.ts        # Export all components
│   └── types.ts        # TypeScript types
├── styles/             # CSS files for vanilla JS widgets
│   ├── button.css     # Radix-themed button CSS
│   ├── theme.css      # Theme tokens (CSS variables)
│   └── index.css      # Combined CSS (optional)
└── utils/              # Utility functions
    └── cn.ts          # className utility (for Tailwind)
```

## Usage

### In React Widgets

```tsx
import { Button } from '@shared/components/Button';

function MyWidget() {
  return <Button variant="primary">Click me</Button>;
}
```

The build system automatically resolves `@shared` to this directory.

### In Vanilla JS Widgets

```javascript
// Use CSS classes
const button = document.createElement('button');
button.className = 'radix-button radix-button--primary';
```

Include the CSS in your Python widget:

```python
widget = anywidget.AnyWidget(
    _esm=pathlib.Path(__file__).parent / "static" / "my-widget.js",
    _css=pathlib.Path(__file__).parent / "static" / "radix-button.css",
)
```

## Adding New Components

1. Create component file in `components/`
2. Export from `components/index.ts`
3. Create corresponding CSS in `styles/` (if needed for vanilla JS)
4. Update build script if needed

## Build Process

- Shared components are bundled into each widget that uses them
- CSS files are copied to `wigglystuff/static/` during build
- No separate shared bundle (each widget is independent)
