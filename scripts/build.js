#!/usr/bin/env node

/**
 * Unified build script for all widgets
 * Handles React/TypeScript widgets, vanilla JS widgets, CSS, and shared components
 */

const esbuild = require('esbuild');
const { readdir, copyFile, mkdir, access } = require('fs/promises');
const { join, dirname, resolve } = require('path');
const { execSync } = require('child_process');
const fs = require('fs');

const ROOT_DIR = resolve(__dirname, '..');
const WIDGETS_DIR = join(ROOT_DIR, 'js');
const OUTPUT_DIR = join(ROOT_DIR, 'wigglystuff/static');
const SHARED_DIR = join(ROOT_DIR, 'js/shared');

// Widget build configuration
const widgets = [
  {
    name: 'copybutton',
    entry: join(WIDGETS_DIR, 'copybutton/widget.tsx'),
    output: join(OUTPUT_DIR, 'copybutton.js'),
    css: join(OUTPUT_DIR, 'copybutton.css'), // Already exists, keep it
    type: 'react',
  },
  {
    name: 'paint',
    entry: join(WIDGETS_DIR, 'paint/widget.tsx'),
    output: join(OUTPUT_DIR, 'paint.js'),
    css: join(WIDGETS_DIR, 'paint/styles.css'), // Tailwind entry
    cssOutput: join(OUTPUT_DIR, 'paint.css'),
    type: 'react',
    tailwind: true,
  },
  {
    name: 'talk',
    entry: join(WIDGETS_DIR, 'talk/widget.js'),
    output: join(OUTPUT_DIR, 'talk-widget.js'),
    css: join(OUTPUT_DIR, 'talk-widget.css'), // Already exists
    type: 'vanilla',
  },
  {
    name: 'keystroke',
    entry: join(WIDGETS_DIR, 'keystroke/widget.js'),
    output: join(OUTPUT_DIR, 'keystroke-widget.js'),
    css: join(OUTPUT_DIR, 'keystroke.css'), // Already exists
    type: 'vanilla',
  },
  {
    name: 'gamepad',
    entry: join(WIDGETS_DIR, 'gamepad/widget.js'),
    output: join(OUTPUT_DIR, 'gamepad-widget.js'),
    type: 'vanilla',
  },
  {
    name: 'driver-tour',
    entry: join(WIDGETS_DIR, 'driver-tour/widget.js'),
    output: join(OUTPUT_DIR, 'driver-tour.js'),
    css: join(WIDGETS_DIR, 'driver-tour/styles.css'),
    cssOutput: join(OUTPUT_DIR, 'driver-tour.css'),
    type: 'vanilla',
  },
  {
    name: 'edgedraw',
    entry: join(WIDGETS_DIR, 'edgedraw.js'),
    output: join(OUTPUT_DIR, 'edgedraw.js'),
    css: join(OUTPUT_DIR, 'edgedraw.css'), // Already exists
    type: 'vanilla',
  },
];

// Shared CSS files to copy (when they exist)
const sharedCSS = [
  {
    src: join(SHARED_DIR, 'styles/button.css'),
    dest: join(OUTPUT_DIR, 'radix-button.css'),
  },
  {
    src: join(SHARED_DIR, 'styles/theme.css'),
    dest: join(OUTPUT_DIR, 'radix-theme.css'),
  },
  {
    src: join(SHARED_DIR, 'styles/index.css'),
    dest: join(OUTPUT_DIR, 'radix-shared.css'),
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
function getReactOptions() {
  return {
    ...baseOptions,
    jsx: 'automatic',
    loader: {
      '.tsx': 'tsx',
      '.ts': 'ts',
    },
    // Externalize React (provided by @anywidget/react)
    external: ['react', 'react-dom'],
    // Alias for shared components
    alias: {
      '@shared': SHARED_DIR,
    },
  };
}

// Check if file exists
async function fileExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

// Build a single widget
async function buildWidget(widget, options = {}) {
  const { watch = false, minify = false } = options;
  
  console.log(`Building ${widget.name}...`);
  
  // Check if entry point exists
  if (!(await fileExists(widget.entry))) {
    console.warn(`⚠ Entry point not found: ${widget.entry}`);
    return null;
  }
  
  // Build JavaScript bundle
  const buildOptions = {
    ...(widget.type === 'react' ? getReactOptions() : baseOptions),
    entryPoints: [widget.entry],
    outfile: widget.output,
    minify,
    watch: watch ? {
      onRebuild(error, result) {
        if (error) {
          console.error(`✗ Error rebuilding ${widget.name}:`, error.message);
        } else {
          console.log(`✓ Rebuilt ${widget.name}`);
          // Rebuild CSS if needed
          if (widget.tailwind && watch) {
            buildWidgetCSS(widget);
          }
        }
      },
    } : false,
  };

  try {
    let context;
    if (watch) {
      context = await esbuild.context(buildOptions);
      await context.watch();
      console.log(`✓ Watching ${widget.name}...`);
    } else {
      await esbuild.build(buildOptions);
      console.log(`✓ Built ${widget.name}`);
    }

    // Handle CSS
    await buildWidgetCSS(widget);

    return context;
  } catch (error) {
    console.error(`✗ Error building ${widget.name}:`, error.message);
    if (!watch) throw error;
    return null;
  }
}

// Build CSS for a widget
async function buildWidgetCSS(widget) {
  if (!widget.css) return;

  try {
    if (widget.tailwind) {
      // Compile Tailwind CSS
      const tailwindInput = widget.css;
      const tailwindOutput = widget.cssOutput || widget.css;
      
      // Ensure output directory exists
      const outputDir = dirname(tailwindOutput);
      await mkdir(outputDir, { recursive: true });
      
      const tailwindCmd = `./node_modules/.bin/tailwindcss -i ${tailwindInput} -o ${tailwindOutput}`;
      execSync(tailwindCmd, { stdio: 'pipe', cwd: ROOT_DIR });
      console.log(`  ✓ Compiled Tailwind CSS for ${widget.name}`);
    } else if (widget.cssOutput && widget.css !== widget.cssOutput) {
      // Copy CSS file if source and destination differ
      if (await fileExists(widget.css)) {
        const outputDir = dirname(widget.cssOutput);
        await mkdir(outputDir, { recursive: true });
        await copyFile(widget.css, widget.cssOutput);
        console.log(`  ✓ Copied CSS for ${widget.name}`);
      }
    }
    // If css points to output and already exists, skip (it's already there)
  } catch (error) {
    console.warn(`  ⚠ CSS build warning for ${widget.name}:`, error.message);
  }
}

// Copy shared CSS files
async function copySharedCSS() {
  console.log('Copying shared CSS...');
  let copied = 0;
  
  for (const css of sharedCSS) {
    if (await fileExists(css.src)) {
      const outputDir = dirname(css.dest);
      await mkdir(outputDir, { recursive: true });
      await copyFile(css.src, css.dest);
      console.log(`  ✓ Copied ${css.src} → ${css.dest}`);
      copied++;
    }
  }
  
  if (copied === 0) {
    console.log('  (No shared CSS files found - this is OK if shared components not yet created)');
  }
  console.log('');
}

// Build all widgets
async function buildAll(options = {}) {
  const { watch = false, minify = false, widgets: widgetFilter } = options;
  
  console.log('='.repeat(60));
  console.log(watch ? 'Watching widgets...' : minify ? 'Building widgets (production)...' : 'Building widgets...');
  console.log('='.repeat(60));
  console.log('');
  
  const widgetsToBuild = widgetFilter 
    ? widgets.filter(w => widgetFilter.includes(w.name))
    : widgets;

  // Ensure output directory exists
  await mkdir(OUTPUT_DIR, { recursive: true });

  // Build shared CSS first (only in non-watch mode)
  if (!watch) {
    await copySharedCSS();
  }

  // Build widgets
  const contexts = [];
  for (const widget of widgetsToBuild) {
    const ctx = await buildWidget(widget, { watch, minify });
    if (ctx) contexts.push(ctx);
  }

  if (watch) {
    console.log('');
    console.log('='.repeat(60));
    console.log('✓ Watching all widgets. Press Ctrl+C to stop.');
    console.log('='.repeat(60));
    
    // Keep process alive
    process.on('SIGINT', async () => {
      console.log('\nStopping watch mode...');
      for (const ctx of contexts) {
        if (ctx) await ctx.dispose();
      }
      process.exit(0);
    });
    
    // Handle errors gracefully in watch mode
    process.on('unhandledRejection', (error) => {
      console.error('Unhandled error:', error.message);
    });
  } else {
    console.log('');
    console.log('='.repeat(60));
    console.log(`✓ Built ${widgetsToBuild.length} widget(s) successfully!`);
    console.log('='.repeat(60));
  }
}

// CLI interface
const args = process.argv.slice(2);
const command = args[0];

if (command === 'watch') {
  const widgetFilter = args[1] ? args[1].split(',') : null;
  buildAll({ watch: true, minify: false, widgets: widgetFilter }).catch((error) => {
    console.error('Build failed:', error);
    process.exit(1);
  });
} else if (command === 'build') {
  const minify = args.includes('--minify');
  const widgetArg = args.find(arg => arg.startsWith('--widgets='));
  const widgetFilter = widgetArg ? widgetArg.split('=')[1].split(',') : null;
  
  buildAll({ watch: false, minify, widgets: widgetFilter }).catch((error) => {
    console.error('Build failed:', error);
    process.exit(1);
  });
} else {
  console.log(`
Widget Build System
===================

Usage:
  node scripts/build.js build [options]
  node scripts/build.js watch [widget1,widget2]

Commands:
  build              Build all widgets
  watch              Watch all widgets for changes

Options:
  --minify           Minify output (production build)
  --widgets=LIST    Build only specified widgets (comma-separated)

Examples:
  node scripts/build.js build                    # Build all widgets
  node scripts/build.js build --minify           # Build all widgets (minified)
  node scripts/build.js build --widgets=paint    # Build only paint widget
  node scripts/build.js build --widgets=paint,copybutton  # Build multiple widgets
  node scripts/build.js watch                    # Watch all widgets
  node scripts/build.js watch paint,copybutton   # Watch specific widgets

Available widgets:
  ${widgets.map(w => w.name).join(', ')}
  `);
}
