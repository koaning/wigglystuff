# Build System Summary: How to Build All Components

## Overview

The build system handles:
1. **React/TypeScript widgets** - Bundled with esbuild, supports JSX
2. **Vanilla JavaScript widgets** - Bundled with esbuild
3. **Shared components** - Bundled into each widget that uses them
4. **CSS files** - Copied or compiled (Tailwind support)
5. **Watch mode** - Automatic rebuilds during development

## Quick Reference

### Build Commands

```bash
# Build all widgets
npm run build

# Build for production (minified)
npm run build:prod

# Watch mode (development)
npm run watch

# Build specific widget(s)
npm run build:widget paint
npm run build:widget paint,copybutton
```

### Makefile Commands (still work)

```bash
# Build all widgets
make js

# Watch mode
make js-watch

# Build specific widget
make js-paint
```

## How It Works

### 1. Widget Configuration

All widgets are configured in `scripts/build.js`:

```javascript
const widgets = [
  {
    name: 'paint',
    entry: 'js/paint/widget.tsx',        // Source file
    output: 'wigglystuff/static/paint.js', // Output file
    css: 'js/paint/styles.css',           // CSS source
    cssOutput: 'wigglystuff/static/paint.css', // CSS output
    type: 'react',                        // or 'vanilla'
    tailwind: true,                       // If using Tailwind
  },
  // ... more widgets
];
```

### 2. Build Process

For each widget:

1. **JavaScript Bundle**
   - React widgets: Uses esbuild with JSX support
   - Vanilla JS: Uses esbuild standard bundling
   - Shared components: Resolved via `@shared` alias, bundled into widget

2. **CSS Processing**
   - Tailwind widgets: Compiled with Tailwind CLI
   - Plain CSS: Copied to output directory
   - Shared CSS: Copied to `wigglystuff/static/`

3. **Output**
   - All files go to `wigglystuff/static/`
   - Matches current structure (no breaking changes)

### 3. Shared Components

**Structure:**
```
js/shared/
├── components/     # React components
├── styles/         # CSS for vanilla JS
└── utils/          # Utility functions
```

**Usage in React:**
```tsx
import { Button } from '@shared/components/Button';
```

**Usage in Vanilla JS:**
```javascript
button.className = 'radix-button radix-button--primary';
```

**Build behavior:**
- Shared components are bundled into each widget
- No separate shared bundle (widgets are independent)
- CSS is copied separately for vanilla JS widgets

## File Flow

```
Source Files                    Build Process                    Output Files
─────────────────              ──────────────                  ──────────────

js/
├── widgets/
│   ├── paint/
│   │   ├── widget.tsx  ──┐
│   │   └── styles.css  ──┤─── esbuild + Tailwind ──→ wigglystuff/static/
│   │                      │                          ├── paint.js
│   └── copybutton/        │                          └── paint.css
│       └── widget.tsx  ───┘
│
└── shared/
    ├── components/
    │   └── Button.tsx  ────┐
    │                       │─── Bundled into widgets ──→ (included in widget.js)
    └── styles/
        └── button.css  ────┘─── Copied ───────────────→ radix-button.css
```

## Adding a New Widget

### Step 1: Create Widget Files

```bash
mkdir -p js/my-widget
touch js/my-widget/widget.tsx  # or .js for vanilla JS
```

### Step 2: Add to Build Config

Edit `scripts/build.js`, add to `widgets` array:

```javascript
{
  name: 'my-widget',
  entry: join(WIDGETS_DIR, 'my-widget/widget.tsx'),
  output: join(OUTPUT_DIR, 'my-widget.js'),
  type: 'react',  // or 'vanilla'
}
```

### Step 3: Build

```bash
npm run build:widget my-widget
```

## Using Shared Components

### Creating a Shared Component

1. **Create component file:**
   ```tsx
   // js/shared/components/Button.tsx
   import * as ButtonPrimitive from "@radix-ui/react-button";
   
   export function Button({ ...props }) {
     return <ButtonPrimitive.Root {...props} />;
   }
   ```

2. **Export from index:**
   ```tsx
   // js/shared/components/index.ts
   export { Button } from './Button';
   ```

3. **Use in widget:**
   ```tsx
   // js/my-widget/widget.tsx
   import { Button } from '@shared/components/Button';
   ```

4. **Build:**
   ```bash
   npm run build:widget my-widget
   ```

The Button component will be automatically bundled into your widget.

## CSS Handling

### Tailwind Widgets

```javascript
{
  name: 'paint',
  css: 'js/paint/styles.css',  // Tailwind entry point
  cssOutput: 'wigglystuff/static/paint.css',
  tailwind: true,
}
```

Build system runs: `tailwindcss -i input.css -o output.css`

### Plain CSS Widgets

```javascript
{
  name: 'driver-tour',
  css: 'js/driver-tour/styles.css',
  cssOutput: 'wigglystuff/static/driver-tour.css',
}
```

Build system copies the CSS file.

### Shared Radix CSS

```javascript
// In scripts/build.js
const sharedCSS = [
  {
    src: 'js/shared/styles/button.css',
    dest: 'wigglystuff/static/radix-button.css',
  },
];
```

Copied automatically during build.

## Development Workflow

### 1. Start Development

```bash
npm run watch
```

### 2. Make Changes

- Edit widget files → Auto-rebuilds
- Edit shared components → Auto-rebuilds widgets that use them
- Edit CSS → Auto-rebuilds (Tailwind recompiles)

### 3. Test

- Widgets are ready in `wigglystuff/static/`
- Refresh your notebook/app

### 4. Production Build

```bash
npm run build:prod
```

Creates minified builds.

## Troubleshooting

### "Entry point not found"
- Check widget entry path in `scripts/build.js`
- Ensure file exists

### Shared components not found
- Check `@shared` alias in build script
- Ensure component is exported from `js/shared/components/index.ts`

### CSS not updating
- Tailwind: CSS rebuilds automatically in watch mode
- Plain CSS: Check file paths

### Build is slow
- First build is slower (subsequent builds are cached)
- Watch mode only rebuilds changed widgets
- Tailwind compilation is the slowest part

## Benefits

✅ **Unified build process** - One command for all widgets  
✅ **Watch mode** - Automatic rebuilds  
✅ **Shared components** - Easy code reuse  
✅ **Production builds** - Minified output  
✅ **Selective builds** - Build only what you need  
✅ **No breaking changes** - Output structure unchanged  

## Next Steps

1. ✅ Build script created (`scripts/build.js`)
2. ✅ Package.json updated with scripts
3. ✅ Shared directory structure created
4. ⏭️ Create shared Button component
5. ⏭️ Migrate widgets to use shared components
6. ⏭️ Update Makefile (optional, scripts work independently)

## Documentation

- **Build System Plan**: `BUILD_SYSTEM_PLAN.md` - Detailed architecture
- **Usage Guide**: `BUILD_SYSTEM_USAGE.md` - How to use the build system
- **Migration Plan**: `RADIX_MIGRATION_PLAN.md` - Radix UI migration strategy
- **Button Analysis**: `RADIX_BUTTON_ANALYSIS.md` - Current button implementations
