# Build System Plan for Radix UI Components

## Current Build System Analysis

### Current State
- **Build Tool**: esbuild (via Makefile targets)
- **Entry Points**: Individual widgets in `js/` directory
- **Output**: `wigglystuff/static/` directory
- **CSS Handling**: Mixed (direct copy, Tailwind compilation)
- **Build Commands**: Individual Makefile targets per widget

### Current Build Targets
```makefile
js-edgedraw:    js/edgedraw.js → wigglystuff/static/edgedraw.js
js-gamepad:     js/gamepad/widget.js → wigglystuff/static/gamepad-widget.js
js-keystroke:   js/keystroke/widget.js → wigglystuff/static/keystroke-widget.js
js-copybutton:  js/copybutton/widget.tsx → wigglystuff/static/copybutton.js
js-talk:         js/talk/widget.js → wigglystuff/static/talk-widget.js
js-driver-tour: js/driver-tour/widget.js + styles.css → wigglystuff/static/
js-paint:       js/paint/widget.tsx + styles.css (Tailwind) → wigglystuff/static/
```

### Issues with Current System
1. **No unified build script** - each widget built separately
2. **No shared component handling** - can't easily share code between widgets
3. **Manual CSS management** - CSS files handled inconsistently
4. **No watch mode** - only one widget has watch mode in package.json
5. **No production build** - no distinction between dev/prod builds

## Proposed Build System Architecture

### Directory Structure
```
js/
├── shared/                    # Shared components and utilities
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── index.ts          # Export all components
│   │   └── types.ts
│   ├── styles/
│   │   ├── button.css        # CSS for vanilla JS widgets
│   │   ├── theme.css         # Theme tokens
│   │   └── index.css         # Combined CSS
│   └── utils/
│       └── cn.ts             # className utility
├── widgets/                   # Individual widget entry points
│   ├── copybutton/
│   │   ├── widget.tsx
│   │   └── styles.css        # Widget-specific styles (if needed)
│   ├── paint/
│   │   ├── widget.tsx
│   │   └── styles.css        # Tailwind entry point
│   ├── talk/
│   │   └── widget.js
│   └── ...
└── legacy/                    # Keep old structure temporarily
    ├── edgedraw.js
    └── ...
```

### Build Configuration

#### Option 1: esbuild-based Build Script (Recommended)
**Pros**: 
- Already using esbuild
- Fast builds
- Simple configuration
- Good TypeScript support

**Cons**:
- Need to write custom build script
- Manual CSS handling

#### Option 2: Vite-based Build System
**Pros**:
- Excellent dev experience
- Built-in CSS handling
- Hot module replacement
- Multi-entry point support

**Cons**:
- Additional dependency
- Might be overkill for widgets

#### Option 3: Hybrid Approach (Recommended)
- Use esbuild for bundling (keep current approach)
- Add unified build script for orchestration
- Use PostCSS for CSS processing
- Add watch mode support

## Implementation: esbuild Build Script

### Build Script: `scripts/build.js`

```javascript
#!/usr/bin/env node

const esbuild = require('esbuild');
const { readdir, copyFile, mkdir } = require('fs/promises');
const { join, dirname } = require('path');
const { execSync } = require('child_process');

const WIDGETS_DIR = join(__dirname, '../js');
const OUTPUT_DIR = join(__dirname, '../wigglystuff/static');
const SHARED_DIR = join(__dirname, '../js/shared');

// Widget build configuration
const widgets = [
  {
    name: 'copybutton',
    entry: 'js/copybutton/widget.tsx',
    output: 'wigglystuff/static/copybutton.js',
    css: 'wigglystuff/static/copybutton.css', // Already exists, keep it
    type: 'react',
  },
  {
    name: 'paint',
    entry: 'js/paint/widget.tsx',
    output: 'wigglystuff/static/paint.js',
    css: 'js/paint/styles.css', // Tailwind entry
    cssOutput: 'wigglystuff/static/paint.css',
    type: 'react',
    tailwind: true,
  },
  {
    name: 'talk',
    entry: 'js/talk/widget.js',
    output: 'wigglystuff/static/talk-widget.js',
    css: 'wigglystuff/static/talk-widget.css', // Already exists
    type: 'vanilla',
  },
  {
    name: 'keystroke',
    entry: 'js/keystroke/widget.js',
    output: 'wigglystuff/static/keystroke-widget.js',
    css: 'wigglystuff/static/keystroke.css', // Already exists
    type: 'vanilla',
  },
  {
    name: 'gamepad',
    entry: 'js/gamepad/widget.js',
    output: 'wigglystuff/static/gamepad-widget.js',
    type: 'vanilla',
  },
  {
    name: 'driver-tour',
    entry: 'js/driver-tour/widget.js',
    output: 'wigglystuff/static/driver-tour.js',
    css: 'js/driver-tour/styles.css',
    cssOutput: 'wigglystuff/static/driver-tour.css',
    type: 'vanilla',
  },
  {
    name: 'edgedraw',
    entry: 'js/edgedraw.js',
    output: 'wigglystuff/static/edgedraw.js',
    css: 'wigglystuff/static/edgedraw.css', // Already exists
    type: 'vanilla',
  },
];

// Shared CSS that needs to be copied to output
const sharedCSS = [
  {
    src: 'js/shared/styles/button.css',
    dest: 'wigglystuff/static/radix-button.css',
  },
  {
    src: 'js/shared/styles/theme.css',
    dest: 'wigglystuff/static/radix-theme.css',
  },
];

// Base esbuild options
const baseOptions = {
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  logLevel: 'info',
};

// React/TypeScript specific options
const reactOptions = {
  ...baseOptions,
  jsx: 'automatic',
  loader: {
    '.tsx': 'tsx',
    '.ts': 'ts',
  },
  external: ['react', 'react-dom'], // React is provided by @anywidget/react
};

// Build a single widget
async function buildWidget(widget, options = {}) {
  const { watch = false, minify = false } = options;
  
  console.log(`Building ${widget.name}...`);
  
  // Build JavaScript bundle
  const buildOptions = {
    ...(widget.type === 'react' ? reactOptions : baseOptions),
    entryPoints: [widget.entry],
    outfile: widget.output,
    minify,
    watch: watch ? {
      onRebuild(error, result) {
        if (error) {
          console.error(`Error rebuilding ${widget.name}:`, error);
        } else {
          console.log(`✓ Rebuilt ${widget.name}`);
        }
      },
    } : false,
  };

  try {
    if (watch) {
      const ctx = await esbuild.context(buildOptions);
      await ctx.watch();
      console.log(`Watching ${widget.name}...`);
      return ctx;
    } else {
      await esbuild.build(buildOptions);
      console.log(`✓ Built ${widget.name}`);
    }
  } catch (error) {
    console.error(`Error building ${widget.name}:`, error);
    throw error;
  }

  // Handle CSS
  if (widget.css) {
    if (widget.tailwind) {
      // Compile Tailwind CSS
      const tailwindCmd = `./node_modules/.bin/tailwindcss -i ${widget.css} -o ${widget.cssOutput || widget.css}`;
      execSync(tailwindCmd, { stdio: 'inherit' });
      console.log(`✓ Compiled Tailwind CSS for ${widget.name}`);
    } else if (widget.cssOutput) {
      // Copy CSS file
      const fs = require('fs');
      fs.copyFileSync(widget.css, widget.cssOutput);
      console.log(`✓ Copied CSS for ${widget.name}`);
    }
    // If css points to output, it already exists, skip
  }
}

// Build all widgets
async function buildAll(options = {}) {
  const { watch = false, minify = false, widgets: widgetFilter } = options;
  
  console.log('Building all widgets...\n');
  
  const widgetsToBuild = widgetFilter 
    ? widgets.filter(w => widgetFilter.includes(w.name))
    : widgets;

  // Build shared CSS first
  if (!watch) {
    console.log('Copying shared CSS...');
    for (const css of sharedCSS) {
      const fs = require('fs');
      if (fs.existsSync(css.src)) {
        fs.copyFileSync(css.src, css.dest);
        console.log(`✓ Copied ${css.src} → ${css.dest}`);
      }
    }
    console.log('');
  }

  // Build widgets
  const contexts = [];
  for (const widget of widgetsToBuild) {
    if (watch) {
      const ctx = await buildWidget(widget, { watch: true, minify });
      if (ctx) contexts.push(ctx);
    } else {
      await buildWidget(widget, { watch: false, minify });
    }
  }

  if (watch) {
    console.log('\n✓ Watching all widgets. Press Ctrl+C to stop.');
    // Keep process alive
    process.on('SIGINT', async () => {
      console.log('\nStopping watch mode...');
      for (const ctx of contexts) {
        await ctx.dispose();
      }
      process.exit(0);
    });
  } else {
    console.log('\n✓ All widgets built successfully!');
  }
}

// CLI interface
const args = process.argv.slice(2);
const command = args[0];

if (command === 'watch') {
  const widgetFilter = args[1] ? args[1].split(',') : null;
  buildAll({ watch: true, minify: false, widgets: widgetFilter });
} else if (command === 'build') {
  const minify = args.includes('--minify');
  const widgetFilter = args.find(arg => arg.startsWith('--widgets='))?.split('=')[1]?.split(',');
  buildAll({ watch: false, minify, widgets: widgetFilter });
} else {
  console.log(`
Usage:
  node scripts/build.js build [--minify] [--widgets=widget1,widget2]
  node scripts/build.js watch [widget1,widget2]

Examples:
  node scripts/build.js build                    # Build all widgets
  node scripts/build.js build --minify           # Build all widgets (minified)
  node scripts/build.js build --widgets=paint    # Build only paint widget
  node scripts/build.js watch                    # Watch all widgets
  node scripts/build.js watch paint,copybutton   # Watch specific widgets
  `);
}
```

### Updated package.json Scripts

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

### Updated Makefile

```makefile
# Build all widgets
js: js-shared
	node scripts/build.js build

# Build for production (minified)
js-prod: js-shared
	node scripts/build.js build --minify

# Watch mode for development
js-watch: js-shared
	node scripts/build.js watch

# Build shared components CSS (if needed)
js-shared:
	@echo "Shared components are bundled automatically"

# Build specific widget
js-%:
	node scripts/build.js build --widgets=$*

# Legacy individual targets (for backward compatibility)
js-edgedraw: js-edgedraw
js-gamepad: js-gamepad
js-keystroke: js-keystroke
js-copybutton: js-copybutton
js-talk: js-talk
js-driver-tour: js-driver-tour
js-paint: js-paint
```

## Handling Shared Components

### Challenge: Bundling Shared Components

When widgets use shared Radix components, we need to ensure:
1. Shared components are bundled into each widget
2. No duplicate React/Radix code across widgets
3. Tree-shaking works correctly

### Solution: External Dependencies + Bundle Shared Code

**Option A: Bundle shared components into each widget** (Current approach)
- Each widget gets its own copy of shared components
- Simpler, but larger bundle sizes
- Works well for widgets that are loaded independently

**Option B: Create shared bundle** (Future optimization)
- Create `wigglystuff/static/shared.js` with common code
- Widgets import from shared bundle
- Requires coordination between widgets

**For now, use Option A** - bundle shared components into each widget.

### esbuild Configuration for Shared Components

```javascript
// In build script, for React widgets:
const reactOptions = {
  ...baseOptions,
  jsx: 'automatic',
  loader: {
    '.tsx': 'tsx',
    '.ts': 'ts',
  },
  // Don't externalize Radix - bundle it
  // Externalize React (provided by @anywidget/react)
  external: ['react', 'react-dom'],
  // Resolve shared components
  alias: {
    '@shared': join(__dirname, '../js/shared'),
  },
};
```

### Import Path Configuration

Create `jsconfig.json` or `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@shared/*": ["js/shared/*"]
    }
  }
}
```

Update esbuild to handle these paths:

```javascript
const { resolve } = require('path');

const reactOptions = {
  // ... other options
  alias: {
    '@shared': resolve(__dirname, '../js/shared'),
  },
};
```

## CSS Build Process

### Shared Radix CSS

1. **Source**: `js/shared/styles/button.css` (Radix-themed CSS)
2. **Output**: `wigglystuff/static/radix-button.css`
3. **Process**: Copy directly (or use PostCSS if needed)

### Widget-Specific CSS

1. **Tailwind widgets** (paint): Compile with Tailwind CLI
2. **Plain CSS widgets**: Copy directly
3. **CSS-in-JS**: Handled by esbuild

### CSS Import Strategy

**For React widgets:**
```tsx
// Import CSS in component
import '../shared/styles/button.css';
// esbuild will handle it
```

**For vanilla JS widgets:**
```javascript
// CSS is separate file, loaded by Python widget
// Just ensure it's copied to output directory
```

## Build Workflow

### Development Workflow

```bash
# Start watch mode for all widgets
npm run watch

# Watch specific widgets
npm run watch paint copybutton

# Build once (dev mode)
npm run build

# Build for production
npm run build:prod
```

### CI/CD Integration

```yaml
# .github/workflows/build.yml
- name: Build widgets
  run: npm run build:prod
```

## Migration Steps

1. **Create build script** (`scripts/build.js`)
2. **Set up shared directory structure** (`js/shared/`)
3. **Update package.json** with new scripts
4. **Update Makefile** to use new build system
5. **Test build** with existing widgets
6. **Migrate widgets** to use shared components one by one
7. **Remove old build targets** once everything works

## Benefits of New Build System

1. ✅ **Unified build process** - One command to build all widgets
2. ✅ **Watch mode** - Automatic rebuilds during development
3. ✅ **Shared components** - Easy to share code between widgets
4. ✅ **Production builds** - Minified builds for production
5. ✅ **Selective builds** - Build only what you need
6. ✅ **Better DX** - Easier to develop and maintain

## Next Steps

1. Create `scripts/build.js` with the build script
2. Set up `js/shared/` directory structure
3. Update `package.json` scripts
4. Update `Makefile`
5. Test with existing widgets
6. Start migrating widgets to use shared components
