# Radix UI Migration Plan

## Executive Summary

This document outlines a plan to introduce Radix UI as a sensible default for all widget components, with a focus on standardizing button implementations across the codebase. Currently, buttons and other UI components are inconsistent, using a mix of custom CSS, Tailwind classes, inline styles, and custom React components.

## Current State Analysis

### Widget Types
1. **React/TypeScript Widgets** (using `@anywidget/react`):
   - `copybutton/widget.tsx` - Plain HTML button with custom CSS classes
   - `paint/widget.tsx` - Custom inline Button component with Tailwind classes

2. **Vanilla JavaScript Widgets**:
   - `talk/widget.js` - Plain HTML button with `.speech-button` CSS class
   - `keystroke/widget.js` - Div with `role="button"` (accessibility concern)
   - `webcam-capture.js` - Plain HTML button with `.webcam-capture__button` CSS class
   - `sortable-list.js` - Plain HTML buttons with `.remove-button` CSS class
   - And others...

### Current Issues

1. **Inconsistent Button Implementations**:
   - Custom CSS classes (`.speech-button`, `.webcam-capture__button`, `.copy-button`)
   - Tailwind utility classes (paint widget)
   - Inline styles (keystroke widget)
   - Custom React components (paint widget)
   - Accessibility issues (divs with role="button" instead of actual buttons)

2. **Styling Inconsistencies**:
   - Different hover states
   - Different active states
   - Different focus states
   - Different disabled states
   - Inconsistent spacing, sizing, and colors

3. **Maintenance Burden**:
   - Each widget maintains its own button styles
   - No shared component library
   - Difficult to maintain consistent UX across widgets

### Current Dependencies

Already installed:
- `@radix-ui/react-icons` (v1.3.2) ✅
- `@radix-ui/themes` (v3.2.1) ✅
- `radix-ui` (v1.1.3) ✅
- `react` (v19.0.0) ✅
- `tailwindcss` (v3.4.18) ✅

## Goals and Benefits

### Primary Goals
1. **Consistency**: Unified button and component styling across all widgets
2. **Accessibility**: Leverage Radix UI's built-in accessibility features
3. **Maintainability**: Single source of truth for component styles
4. **Developer Experience**: Easier to create new widgets with consistent components
5. **User Experience**: Consistent, polished UI across all widgets

### Benefits
- **Accessibility**: Radix UI components follow WAI-ARIA guidelines
- **Theming**: Built-in support for light/dark themes via `@radix-ui/themes`
- **Customization**: Flexible styling system that works with Tailwind
- **Type Safety**: Better TypeScript support for React components
- **Bundle Size**: Tree-shakeable, only import what you need

## Migration Strategy

### Phase 1: Foundation (Week 1)
**Goal**: Set up shared component library and design system

1. **Install Additional Radix UI Primitives**
   ```bash
   npm install @radix-ui/react-button @radix-ui/react-slot
   ```

2. **Create Shared Component Library**
   - Create `js/shared/components/` directory
   - Build reusable Button component using Radix UI primitives
   - Create other common components (if needed): Input, Select, etc.
   - Set up theming configuration

3. **Create Design Tokens**
   - Define color palette
   - Define spacing scale
   - Define typography scale
   - Define component variants (sizes, styles)

### Phase 2: React Widget Migration (Week 2)
**Goal**: Migrate React/TypeScript widgets to use shared components

1. **Migrate `copybutton/widget.tsx`**
   - Replace custom button with Radix Button component
   - Update CSS to use Radix theme tokens
   - Test functionality

2. **Migrate `paint/widget.tsx`**
   - Replace inline Button component with shared Radix Button
   - Consolidate button variants
   - Update all button usages in the widget

### Phase 3: Vanilla JS Widget Strategy (Week 3)
**Goal**: Create a strategy for vanilla JS widgets

**Option A: CSS-Only Approach** (Recommended for now)
- Create Radix-themed CSS classes that vanilla JS can use
- Build a CSS utility library matching Radix button styles
- Keep vanilla JS widgets using plain HTML buttons but with Radix-styled classes

**Option B: Hybrid Approach** (Future consideration)
- Convert vanilla JS widgets to React where it makes sense
- Use shared React components for new widgets
- Gradually migrate existing widgets

**Decision**: Start with **Option A** for minimal disruption, but design CSS classes to match Radix component styles.

### Phase 4: Documentation & Guidelines (Week 4)
**Goal**: Document the new system and create guidelines

1. **Create Component Documentation**
   - Document shared Button component API
   - Provide usage examples
   - Document theming approach

2. **Create Migration Guide**
   - Step-by-step guide for migrating widgets
   - Common patterns and examples
   - Troubleshooting guide

3. **Update Development Guidelines**
   - When to use Radix components
   - When to use vanilla HTML + CSS
   - Styling conventions

## Implementation Details

### Shared Button Component Structure

```
js/shared/
├── components/
│   ├── Button.tsx          # Main Button component
│   ├── index.ts            # Exports
│   └── types.ts            # TypeScript types
├── styles/
│   ├── button.css          # CSS for vanilla JS widgets
│   └── theme.css           # Theme tokens
└── utils/
    └── cn.ts               # className utility (if needed)
```

### Button Component API

```typescript
interface ButtonProps {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children: React.ReactNode;
  // ... other standard button props
}
```

### CSS Classes for Vanilla JS

```css
/* Radix-themed button classes */
.radix-button { /* base styles */ }
.radix-button--primary { /* variant */ }
.radix-button--secondary { /* variant */ }
.radix-button--ghost { /* variant */ }
.radix-button--sm { /* size */ }
.radix-button--md { /* size */ }
.radix-button--lg { /* size */ }
```

## Migration Checklist

### Foundation
- [ ] Install `@radix-ui/react-button` and `@radix-ui/react-slot`
- [ ] Create `js/shared/components/` directory structure
- [ ] Build shared Button component with Radix UI
- [ ] Create CSS classes for vanilla JS widgets
- [ ] Set up theme configuration
- [ ] Test shared components in isolation

### React Widgets
- [ ] Migrate `copybutton/widget.tsx`
  - [ ] Replace button with Radix Button
  - [ ] Update CSS/styling
  - [ ] Test functionality
  - [ ] Verify accessibility
- [ ] Migrate `paint/widget.tsx`
  - [ ] Replace inline Button component
  - [ ] Update all button instances
  - [ ] Test functionality
  - [ ] Verify accessibility

### Vanilla JS Widgets
- [ ] Update `talk/widget.js`
  - [ ] Replace `.speech-button` with Radix CSS classes
  - [ ] Test functionality
- [ ] Update `webcam-capture.js`
  - [ ] Replace `.webcam-capture__button` with Radix CSS classes
  - [ ] Test functionality
- [ ] Update `sortable-list.js`
  - [ ] Replace `.remove-button` with Radix CSS classes
  - [ ] Test functionality
- [ ] Update `keystroke/widget.js`
  - [ ] Replace div with role="button" with actual button
  - [ ] Apply Radix CSS classes
  - [ ] Test functionality
- [ ] Review other widgets for button usage

### Documentation
- [ ] Document shared Button component
- [ ] Create migration guide
- [ ] Update development guidelines
- [ ] Add examples to README or docs

### Testing & Quality
- [ ] Test all migrated widgets
- [ ] Verify accessibility (keyboard navigation, screen readers)
- [ ] Verify theming (light/dark mode)
- [ ] Check bundle size impact
- [ ] Update tests if needed

## Considerations

### Bundle Size
- Radix UI is modular and tree-shakeable
- Only import what's needed
- Monitor bundle size after migration

### Backward Compatibility
- Ensure existing widgets continue to work
- CSS classes should be additive, not breaking
- Consider versioning if needed

### Theming
- Leverage `@radix-ui/themes` for consistent theming
- Support both light and dark modes
- Ensure CSS classes respect theme variables

### Performance
- Radix UI components are performant
- No significant performance impact expected
- Test on slower devices if possible

## Future Enhancements

1. **Additional Radix Components**: Consider migrating other components (Select, Dialog, etc.)
2. **Component Storybook**: Create a component library documentation site
3. **Design System**: Expand beyond buttons to create a full design system
4. **Widget Templates**: Create starter templates using Radix components
5. **Automated Testing**: Add visual regression testing for components

## Timeline

- **Week 1**: Foundation setup
- **Week 2**: React widget migration
- **Week 3**: Vanilla JS widget migration
- **Week 4**: Documentation and polish

**Total Estimated Time**: 4 weeks (can be done incrementally)

## Success Metrics

1. ✅ All widgets use consistent button styling
2. ✅ Zero accessibility violations for buttons
3. ✅ All widgets support light/dark themes
4. ✅ Reduced CSS duplication
5. ✅ Developer satisfaction with component library

## Next Steps

1. Review and approve this plan
2. Set up development branch
3. Begin Phase 1: Foundation setup
4. Create first shared Button component
5. Migrate first widget as proof of concept
