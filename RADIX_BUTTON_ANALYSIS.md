# Button Implementation Analysis

## Current Button Implementations Across Widgets

### 1. Copy Button (`copybutton/widget.tsx`)
**Type**: React/TypeScript  
**Implementation**: Plain HTML button with custom CSS class

```tsx
<button 
    className="copy-button"
    onClick={() => copyToClipboard(text_to_copy)}
    type="button"
>
    <CopyIcon className="copy-button-icon" />
    Copy to Clipboard
</button>
```

**CSS**: Custom `.copy-button` class with CSS variables for theming
- Has hover, active, focus, disabled states
- Uses CSS variables for theming
- Supports dark mode

**Issues**: 
- ✅ Good accessibility (actual button element)
- ✅ Good theming support
- ❌ Custom implementation, not reusable

---

### 2. Paint Widget (`paint/widget.tsx`)
**Type**: React/TypeScript  
**Implementation**: Custom inline Button component

```tsx
const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'default' | 'ghost'
  }
>(({ className = '', variant = 'default', ...props }, ref) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-md text-sm font-medium focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50';
  const variantStyles = {
    default: 'bg-gray-200 active:bg-gray-300',
    ghost: 'active:bg-gray-100/50'
  };
  
  return (
    <button
      ref={ref}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      {...props}
    />
  );
});
```

**Usage**: Multiple instances with different variants
- Tool buttons (brush, marker, eraser)
- Window controls
- Color picker buttons
- Clear button

**Issues**:
- ✅ Reusable within widget
- ✅ TypeScript support
- ❌ Not shared across widgets
- ❌ Limited variants
- ❌ Uses Tailwind (not consistent with other widgets)

---

### 3. Talk Widget (`talk/widget.js`)
**Type**: Vanilla JavaScript  
**Implementation**: Plain HTML button with CSS class

```javascript
const button = document.createElement('button');
button.className = 'speech-button';
button.textContent = model.get('listening') ? 'Stop Listening' : 'Start Listening';
```

**CSS**: `.speech-button` class
```css
.speech-button {
  padding: 10px 20px;
  background: #4285f4;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s ease;
}
```

**Issues**:
- ✅ Actual button element
- ❌ Hard-coded colors (not themeable)
- ❌ Custom implementation
- ❌ No dark mode support

---

### 4. Webcam Capture (`webcam-capture.js`)
**Type**: Vanilla JavaScript  
**Implementation**: Plain HTML button with CSS class

```javascript
const captureButton = document.createElement("button");
captureButton.type = "button";
captureButton.className = "webcam-capture__button";
captureButton.textContent = "Capture";
```

**CSS**: `.webcam-capture__button` class
```css
.webcam-capture__button {
    border: none;
    padding: 10px 18px;
    border-radius: 999px;
    font-weight: 600;
    color: #ffffff;
    background: var(--webcam-accent, #0ea5e9);
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    box-shadow: 0 6px 16px rgba(14, 165, 233, 0.35);
}
```

**Issues**:
- ✅ Uses CSS variables (themeable)
- ✅ Actual button element
- ❌ Custom implementation
- ❌ Different styling from other buttons

---

### 5. Sortable List (`sortable-list.js`)
**Type**: Vanilla JavaScript  
**Implementation**: Plain HTML button for remove action

```javascript
removeButton = document.createElement("button");
removeButton.className = "remove-button";
removeButton.innerHTML = `×`;
removeButton.setAttribute("aria-label", `Remove ${item}`);
```

**CSS**: `.remove-button` class
```css
.remove-button {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--sortable-text-button-hover);
}
```

**Issues**:
- ✅ Actual button element
- ✅ Good accessibility (aria-label)
- ✅ Uses CSS variables
- ❌ Custom implementation

---

### 6. Keystroke Widget (`keystroke/widget.js`)
**Type**: Vanilla JavaScript  
**Implementation**: Div with `role="button"` ⚠️

```javascript
const keyCanvas = document.createElement("div");
keyCanvas.setAttribute("role", "button");
keyCanvas.setAttribute("aria-label", "Capture keyboard shortcut");
keyCanvas.tabIndex = 0;
```

**Issues**:
- ❌ **Accessibility concern**: Not an actual button element
- ❌ Should be converted to actual button
- ❌ Custom styling approach

---

## Summary of Issues

### Consistency Problems
1. **Different styling approaches**: Custom CSS, Tailwind, inline styles
2. **Different color schemes**: Hard-coded colors vs CSS variables
3. **Different sizes**: No standard sizing scale
4. **Different hover/active states**: Inconsistent interactions
5. **Different focus states**: Accessibility inconsistencies

### Accessibility Issues
1. **Keystroke widget**: Uses div instead of button
2. **Inconsistent focus management**: Some widgets may not handle keyboard navigation well
3. **Missing ARIA attributes**: Not all buttons have proper labels

### Maintenance Issues
1. **Code duplication**: Each widget maintains its own button styles
2. **No shared component**: Can't reuse button logic
3. **Hard to update**: Changes require updating multiple files

## Proposed Solution: Radix UI Button

### For React Widgets

```tsx
// js/shared/components/Button.tsx
import * as React from "react";
import * as ButtonPrimitive from "@radix-ui/react-button";
import { cn } from "../utils/cn";

interface ButtonProps extends React.ComponentPropsWithoutRef<typeof ButtonPrimitive.Root> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

const Button = React.forwardRef<
  React.ElementRef<typeof ButtonPrimitive.Root>,
  ButtonProps
>(({ className, variant = 'default', size = 'md', ...props }, ref) => {
  return (
    <ButtonPrimitive.Root
      ref={ref}
      className={cn(
        // Base styles
        "inline-flex items-center justify-center rounded-md font-medium",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        // Size variants
        {
          'sm': 'h-8 px-3 text-sm',
          'md': 'h-10 px-4 text-sm',
          'lg': 'h-12 px-6 text-base',
        }[size],
        // Variant styles
        {
          'default': 'bg-gray-200 text-gray-900 hover:bg-gray-300',
          'primary': 'bg-blue-600 text-white hover:bg-blue-700',
          'secondary': 'bg-gray-100 text-gray-900 hover:bg-gray-200',
          'ghost': 'hover:bg-gray-100',
          'danger': 'bg-red-600 text-white hover:bg-red-700',
        }[variant],
        className
      )}
      {...props}
    />
  );
});

Button.displayName = "Button";

export { Button };
```

### For Vanilla JS Widgets

```css
/* js/shared/styles/button.css */
.radix-button {
  /* Base styles matching Radix Button component */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  outline: none;
}

.radix-button:focus-visible {
  outline: 2px solid var(--radix-button-focus-ring);
  outline-offset: 2px;
}

.radix-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* Size variants */
.radix-button--sm {
  height: 32px;
  padding: 0 12px;
  font-size: 14px;
}

.radix-button--md {
  height: 40px;
  padding: 0 16px;
  font-size: 14px;
}

.radix-button--lg {
  height: 48px;
  padding: 0 24px;
  font-size: 16px;
}

/* Variant styles */
.radix-button--default {
  background-color: var(--radix-button-default-bg, #e5e7eb);
  color: var(--radix-button-default-text, #111827);
}

.radix-button--default:hover {
  background-color: var(--radix-button-default-bg-hover, #d1d5db);
}

.radix-button--primary {
  background-color: var(--radix-button-primary-bg, #2563eb);
  color: var(--radix-button-primary-text, #ffffff);
}

.radix-button--primary:hover {
  background-color: var(--radix-button-primary-bg-hover, #1d4ed8);
}

.radix-button--ghost {
  background-color: transparent;
  color: var(--radix-button-ghost-text, #374151);
}

.radix-button--ghost:hover {
  background-color: var(--radix-button-ghost-bg-hover, #f3f4f6);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .radix-button--default {
    background-color: var(--radix-button-default-bg-dark, #374151);
    color: var(--radix-button-default-text-dark, #f9fafb);
  }
  
  /* ... other dark mode variants */
}
```

### Usage Examples

**React Widget:**
```tsx
import { Button } from '../shared/components/Button';

<Button variant="primary" size="md" onClick={handleClick}>
  Click me
</Button>
```

**Vanilla JS Widget:**
```javascript
const button = document.createElement('button');
button.className = 'radix-button radix-button--primary radix-button--md';
button.textContent = 'Click me';
```

## Migration Priority

1. **High Priority** (Accessibility issues):
   - Keystroke widget (div → button)

2. **Medium Priority** (React widgets - easier migration):
   - Copy button widget
   - Paint widget

3. **Low Priority** (Vanilla JS - CSS-only migration):
   - Talk widget
   - Webcam capture widget
   - Sortable list widget
