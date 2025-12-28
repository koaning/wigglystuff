# Build System Usage Guide

## Quick Start

### Build All Widgets
```bash
npm run build
```

### Build for Production (Minified)
```bash
npm run build:prod
```

### Watch Mode (Development)
```bash
npm run watch
```

### Build Specific Widget(s)
```bash
npm run build:widget paint
npm run build:widget paint,copybutton
```

## Available Scripts

After updating `package.json`, you'll have:

```json
{
  "scripts": {
    "build": "node scripts/build.js build",
    "build:prod": "node scripts/build.js build --minify",
    "build:widget": "node scripts/build.js build --widgets",
    "watch": "node scripts/build.js watch",
    "watch:widget": "node scripts/build.js watch",
    "dev": "npm run watch"
  }
}
```

## Build Process

### What Gets Built

1. **JavaScript/TypeScript Widgets**
   - React widgets (`.tsx`) → Bundled with esbuild
   - Vanilla JS widgets (`.js`) → Bundled with esbuild
   - Shared components → Bundled into each widget that uses them

2. **CSS Files**
   - Tailwind widgets → Compiled with Tailwind CLI
   - Plain CSS → Copied to output directory
   - Shared Radix CSS → Copied to `wigglystuff/static/`

3. **Output Location**
   - All built files go to `wigglystuff/static/`
   - This matches the current structure

## Widget Configuration

Widgets are configured in `scripts/build.js`:

```javascript
{
  name: 'widget-name',
  entry: 'js/widget-name/widget.tsx',  // Source file
  output: 'wigglystuff/static/widget-name.js',  // Output file
  css: 'path/to/styles.css',  // CSS source (optional)
  cssOutput: 'wigglystuff/static/widget-name.css',  // CSS output (optional)
  type: 'react',  // or 'vanilla'
  tailwind: true,  // If using Tailwind CSS
}
```

## Adding a New Widget

1. **Create widget file** in `js/your-widget/`
2. **Add configuration** to `scripts/build.js` widgets array
3. **Run build**: `npm run build:widget your-widget`

### Example: Adding a React Widget

```javascript
// In scripts/build.js, add to widgets array:
{
  name: 'my-widget',
  entry: join(WIDGETS_DIR, 'my-widget/widget.tsx'),
  output: join(OUTPUT_DIR, 'my-widget.js'),
  type: 'react',
}
```

### Example: Adding a Vanilla JS Widget

```javascript
{
  name: 'my-widget',
  entry: join(WIDGETS_DIR, 'my-widget/widget.js'),
  output: join(OUTPUT_DIR, 'my-widget.js'),
  css: join(WIDGETS_DIR, 'my-widget/styles.css'),
  cssOutput: join(OUTPUT_DIR, 'my-widget.css'),
  type: 'vanilla',
}
```

## Using Shared Components

### In React Widgets

```tsx
// js/my-widget/widget.tsx
import { Button } from '@shared/components/Button';

function MyWidget() {
  return (
    <Button variant="primary" onClick={handleClick}>
      Click me
    </Button>
  );
}
```

The build system will:
1. Resolve `@shared` alias to `js/shared/`
2. Bundle the Button component into your widget
3. Handle all dependencies automatically

### In Vanilla JS Widgets

```javascript
// Use Radix CSS classes
const button = document.createElement('button');
button.className = 'radix-button radix-button--primary radix-button--md';
button.textContent = 'Click me';
```

Make sure to include the Radix CSS in your widget's Python file:

```python
# wigglystuff/my_widget.py
import anywidget
import pathlib

widget = anywidget.AnyWidget(
    _esm=pathlib.Path(__file__).parent / "static" / "my-widget.js",
    _css=pathlib.Path(__file__).parent / "static" / "radix-button.css",  # Include shared CSS
)
```

## Development Workflow

### 1. Start Development
```bash
npm run watch
```

This will:
- Watch all widget files for changes
- Automatically rebuild when files change
- Show build errors in real-time

### 2. Make Changes
- Edit widget files in `js/`
- Edit shared components in `js/shared/`
- Build system automatically rebuilds

### 3. Test Changes
- Widgets are rebuilt automatically
- Refresh your notebook/app to see changes

### 4. Production Build
```bash
npm run build:prod
```

This creates minified, optimized builds for production.

## Troubleshooting

### Build Fails: "Entry point not found"
- Check that the widget entry path in `scripts/build.js` is correct
- Ensure the file exists in `js/` directory

### Shared Components Not Found
- Check that `js/shared/components/` exists
- Verify the `@shared` alias in build script
- Ensure shared components are exported from `js/shared/components/index.ts`

### CSS Not Updating
- For Tailwind widgets: CSS is rebuilt automatically in watch mode
- For plain CSS: Ensure CSS file is copied correctly
- Check that CSS output path is correct

### Watch Mode Not Working
- Ensure you're using Node.js 14+ (for esbuild context API)
- Check that files are being saved (not just modified)
- Try restarting watch mode

## Integration with Makefile

The Makefile can still be used:

```makefile
# Build all widgets
js:
	npm run build

# Watch mode
js-watch:
	npm run watch

# Build specific widget
js-paint:
	npm run build:widget paint
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build widgets
  run: |
    npm ci
    npm run build:prod
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
npm run build
git add wigglystuff/static/
```

## Performance Considerations

### Bundle Size
- Each widget bundles its own copy of shared components
- This is intentional for widget independence
- Future optimization: Create shared bundle if needed

### Build Speed
- esbuild is very fast (usually < 1 second for all widgets)
- Watch mode only rebuilds changed widgets
- Tailwind compilation is the slowest part (still fast)

### Production Optimization
- Use `--minify` flag for production builds
- Consider code splitting for large widgets
- Monitor bundle sizes

## Next Steps

1. **Set up shared components** (`js/shared/components/`)
2. **Create Button component** using Radix UI
3. **Migrate widgets** one by one to use shared components
4. **Update documentation** as you add more shared components
