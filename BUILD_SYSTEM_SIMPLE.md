# Simple Build System: One Widget at a Time

## Overview

Since we only build one widget at a time, we can use esbuild directly with proper configuration for shared components. Much simpler!

## Current Approach (Makefile)

The Makefile already builds widgets individually:

```makefile
js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx --bundle --format=esm --outfile=wigglystuff/static/paint.js --minify
```

## Simple Solution: esbuild with Alias

We just need to configure esbuild to resolve `@shared` imports. Two options:

### Option 1: esbuild.config.js (Recommended)

Create a simple config file that esbuild can use:

```javascript
// esbuild.config.js
const { resolve } = require('path');

module.exports = {
  alias: {
    '@shared': resolve(__dirname, 'js/shared'),
  },
  // Base options
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  external: ['react', 'react-dom'], // React provided by @anywidget/react
};
```

Then use it in Makefile:

```makefile
js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		--bundle --format=esm \
		--outfile=wigglystuff/static/paint.js \
		--alias:@shared=./js/shared \
		--jsx=automatic \
		--minify
```

### Option 2: Simple Build Script per Widget

Create a small script that wraps esbuild with the right config:

```javascript
// scripts/build-widget.js
const esbuild = require('esbuild');
const { resolve } = require('path');

const widget = process.argv[2];
const watch = process.argv.includes('--watch');
const minify = process.argv.includes('--minify');

const configs = {
  paint: {
    entry: 'js/paint/widget.tsx',
    output: 'wigglystuff/static/paint.js',
    css: { input: 'js/paint/styles.css', output: 'wigglystuff/static/paint.css', tailwind: true },
    jsx: 'automatic',
  },
  copybutton: {
    entry: 'js/copybutton/widget.tsx',
    output: 'wigglystuff/static/copybutton.js',
    jsx: 'automatic',
  },
  // ... other widgets
};

const config = configs[widget];
if (!config) {
  console.error(`Unknown widget: ${widget}`);
  process.exit(1);
}

// Build JS
esbuild.build({
  entryPoints: [config.entry],
  outfile: config.output,
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  jsx: config.jsx || undefined,
  alias: {
    '@shared': resolve(__dirname, '..', 'js/shared'),
  },
  external: ['react', 'react-dom'],
  minify,
  watch: watch ? {
    onRebuild(error) {
      if (error) console.error('Build failed:', error);
      else console.log(`✓ Rebuilt ${widget}`);
    },
  } : false,
}).then(() => {
  console.log(`✓ Built ${widget}`);
  
  // Handle CSS if needed
  if (config.css) {
    if (config.css.tailwind) {
      const { execSync } = require('child_process');
      execSync(`./node_modules/.bin/tailwindcss -i ${config.css.input} -o ${config.css.output}`);
      console.log(`✓ Compiled CSS for ${widget}`);
    }
  }
}).catch(() => process.exit(1));
```

Usage:
```bash
node scripts/build-widget.js paint --watch
node scripts/build-widget.js copybutton --minify
```

## Recommended: Keep It Simple with Makefile

Since you're already using Makefile, just update it to support `@shared` alias:

```makefile
# Base esbuild options with shared alias
ESBUILD_BASE = --bundle --format=esm --alias:@shared=./js/shared
ESBUILD_REACT = $(ESBUILD_BASE) --jsx=automatic --external:react --external:react-dom

js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		$(ESBUILD_REACT) \
		--outfile=wigglystuff/static/paint.js \
		--minify

js-copybutton:
	./node_modules/.bin/esbuild js/copybutton/widget.tsx \
		$(ESBUILD_REACT) \
		--outfile=wigglystuff/static/copybutton.js \
		--minify

js-talk:
	./node_modules/.bin/esbuild js/talk/widget.js \
		$(ESBUILD_BASE) \
		--outfile=wigglystuff/static/talk-widget.js \
		--minify

# Watch mode
js-paint-watch:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css --watch &
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		$(ESBUILD_REACT) \
		--outfile=wigglystuff/static/paint.js \
		--watch
```

## Even Simpler: Just Use esbuild Directly

For shared components, you can use relative imports instead of `@shared`:

```tsx
// In js/paint/widget.tsx
import { Button } from '../shared/components/Button';
```

Then no alias needed! Just:

```makefile
js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx \
		--bundle --format=esm \
		--jsx=automatic \
		--external:react --external:react-dom \
		--outfile=wigglystuff/static/paint.js \
		--minify
```

## Recommendation

**Use relative imports** - simplest, no config needed:

```tsx
// js/paint/widget.tsx
import { Button } from '../shared/components/Button';
```

```tsx
// js/copybutton/widget.tsx  
import { Button } from '../shared/components/Button';
```

Then your Makefile stays simple, just add `--jsx=automatic` for React widgets and you're done!
