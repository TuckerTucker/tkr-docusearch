# UI Design Contract

**Provider**: ui-styling-agent
**Consumers**: ui-static-setup-agent (read-only), upload-logic-agent (state classes)
**Wave**: 2
**Status**: Specification

## Overview

Defines the visual design system, CSS architecture, and styling standards for the custom upload interface. All styling must be responsive, accessible, and maintainable.

## Design System

### Color Palette

#### Primary Colors
```css
:root {
    /* Primary brand colors */
    --color-primary: #2563eb;        /* Blue 600 */
    --color-primary-hover: #1d4ed8;  /* Blue 700 */
    --color-primary-light: #dbeafe;  /* Blue 100 */

    /* Success states */
    --color-success: #16a34a;        /* Green 600 */
    --color-success-light: #dcfce7;  /* Green 100 */

    /* Error states */
    --color-error: #dc2626;          /* Red 600 */
    --color-error-light: #fee2e2;    /* Red 100 */

    /* Warning states */
    --color-warning: #ea580c;        /* Orange 600 */
    --color-warning-light: #ffedd5;  /* Orange 100 */

    /* Neutral colors */
    --color-neutral-50: #fafafa;
    --color-neutral-100: #f5f5f5;
    --color-neutral-200: #e5e5e5;
    --color-neutral-300: #d4d4d4;
    --color-neutral-400: #a3a3a3;
    --color-neutral-500: #737373;
    --color-neutral-600: #525252;
    --color-neutral-700: #404040;
    --color-neutral-800: #262626;
    --color-neutral-900: #171717;

    /* Text colors */
    --color-text-primary: var(--color-neutral-900);
    --color-text-secondary: var(--color-neutral-600);
    --color-text-muted: var(--color-neutral-500);

    /* Background colors */
    --color-bg-primary: #ffffff;
    --color-bg-secondary: var(--color-neutral-50);
    --color-bg-tertiary: var(--color-neutral-100);

    /* Border colors */
    --color-border: var(--color-neutral-200);
    --color-border-dark: var(--color-neutral-300);
}
```

#### Dark Mode (Optional Enhancement)
```css
@media (prefers-color-scheme: dark) {
    :root {
        --color-text-primary: var(--color-neutral-50);
        --color-text-secondary: var(--color-neutral-300);
        --color-bg-primary: var(--color-neutral-900);
        --color-bg-secondary: var(--color-neutral-800);
        --color-bg-tertiary: var(--color-neutral-700);
        --color-border: var(--color-neutral-700);
        --color-border-dark: var(--color-neutral-600);
    }
}
```

---

### Typography

```css
:root {
    /* Font families */
    --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Helvetica Neue", Arial, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
                 "Liberation Mono", monospace;

    /* Font sizes */
    --text-xs: 0.75rem;      /* 12px */
    --text-sm: 0.875rem;     /* 14px */
    --text-base: 1rem;       /* 16px */
    --text-lg: 1.125rem;     /* 18px */
    --text-xl: 1.25rem;      /* 20px */
    --text-2xl: 1.5rem;      /* 24px */
    --text-3xl: 1.875rem;    /* 30px */
    --text-4xl: 2.25rem;     /* 36px */

    /* Font weights */
    --font-normal: 400;
    --font-medium: 500;
    --font-semibold: 600;
    --font-bold: 700;

    /* Line heights */
    --leading-tight: 1.25;
    --leading-normal: 1.5;
    --leading-relaxed: 1.75;
}

body {
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: var(--leading-normal);
    color: var(--color-text-primary);
}

h1 { font-size: var(--text-3xl); font-weight: var(--font-bold); line-height: var(--leading-tight); }
h2 { font-size: var(--text-2xl); font-weight: var(--font-semibold); line-height: var(--leading-tight); }
h3 { font-size: var(--text-xl); font-weight: var(--font-semibold); line-height: var(--leading-tight); }

.text-muted { color: var(--color-text-muted); }
.text-secondary { color: var(--color-text-secondary); }
```

---

### Spacing System

```css
:root {
    /* Spacing scale (4px base) */
    --space-1: 0.25rem;   /* 4px */
    --space-2: 0.5rem;    /* 8px */
    --space-3: 0.75rem;   /* 12px */
    --space-4: 1rem;      /* 16px */
    --space-5: 1.25rem;   /* 20px */
    --space-6: 1.5rem;    /* 24px */
    --space-8: 2rem;      /* 32px */
    --space-10: 2.5rem;   /* 40px */
    --space-12: 3rem;     /* 48px */
    --space-16: 4rem;     /* 64px */
    --space-20: 5rem;     /* 80px */

    /* Border radius */
    --radius-sm: 0.25rem;   /* 4px */
    --radius-md: 0.375rem;  /* 6px */
    --radius-lg: 0.5rem;    /* 8px */
    --radius-xl: 0.75rem;   /* 12px */
    --radius-2xl: 1rem;     /* 16px */
    --radius-full: 9999px;

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
}
```

---

### Layout

```css
/* Container */
.app-main {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--space-6);
}

/* Responsive grid */
@media (min-width: 768px) {
    .app-main {
        padding: var(--space-8);
    }
}

@media (min-width: 1024px) {
    .app-main {
        padding: var(--space-12);
    }
}
```

---

## Component Styles

### Drop Zone

```css
.drop-zone {
    border: 2px dashed var(--color-border-dark);
    border-radius: var(--radius-xl);
    padding: var(--space-12);
    text-align: center;
    background: var(--color-bg-secondary);
    transition: all 0.2s ease;
    cursor: pointer;
}

.drop-zone:hover {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
}

.drop-zone--active {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
    border-style: solid;
    transform: scale(1.02);
}

.drop-zone--error {
    border-color: var(--color-error);
    background: var(--color-error-light);
}

.drop-zone-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto var(--space-4);
    color: var(--color-neutral-400);
}

.drop-zone-text {
    font-size: var(--text-lg);
    color: var(--color-text-secondary);
}

.file-input {
    display: none;
}

.file-input-label {
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
}

.file-input-label:hover {
    color: var(--color-primary-hover);
}
```

---

### Progress Bar

```css
.progress-bar {
    width: 100%;
    height: 8px;
    background: var(--color-neutral-200);
    border-radius: var(--radius-full);
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary), var(--color-primary-hover));
    border-radius: var(--radius-full);
    transition: width 0.3s ease;
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { opacity: 0.8; }
    50% { opacity: 1; }
    100% { opacity: 0.8; }
}

.progress-text {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    margin-top: var(--space-2);
    display: block;
}
```

---

### Queue Items

```css
.queue-items {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
}

.queue-item {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    transition: all 0.2s ease;
}

.queue-item:hover {
    box-shadow: var(--shadow-md);
}

.queue-item--processing {
    border-left: 4px solid var(--color-primary);
}

.queue-item--completed {
    border-left: 4px solid var(--color-success);
    opacity: 0.7;
}

.queue-item--failed {
    border-left: 4px solid var(--color-error);
}

.queue-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-3);
}

.queue-item-filename {
    font-size: var(--text-base);
    font-weight: var(--font-medium);
    margin: 0;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.queue-item-status {
    font-size: var(--text-sm);
    font-weight: var(--font-medium);
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius-full);
    background: var(--color-neutral-100);
    color: var(--color-text-secondary);
}

.queue-item--processing .queue-item-status {
    background: var(--color-primary-light);
    color: var(--color-primary);
}

.queue-item--completed .queue-item-status {
    background: var(--color-success-light);
    color: var(--color-success);
}

.queue-item--failed .queue-item-status {
    background: var(--color-error-light);
    color: var(--color-error);
}

.queue-item-details {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-sm);
    color: var(--color-text-muted);
    margin-top: var(--space-2);
}
```

---

### Toast Notifications

```css
.toast-container {
    position: fixed;
    bottom: var(--space-6);
    right: var(--space-6);
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    max-width: 400px;
}

.toast {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    box-shadow: var(--shadow-lg);
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.toast--success {
    border-left: 4px solid var(--color-success);
}

.toast--error {
    border-left: 4px solid var(--color-error);
}

.toast--warning {
    border-left: 4px solid var(--color-warning);
}

.toast-message {
    font-size: var(--text-sm);
    margin: 0;
}
```

---

## Responsive Design

### Mobile (320px - 767px)

```css
@media (max-width: 767px) {
    .app-main {
        padding: var(--space-4);
    }

    .drop-zone {
        padding: var(--space-8);
    }

    .queue-item-header {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--space-2);
    }

    .queue-item-details {
        flex-direction: column;
        gap: var(--space-1);
    }

    .toast-container {
        left: var(--space-4);
        right: var(--space-4);
        max-width: none;
    }
}
```

### Tablet (768px - 1023px)

```css
@media (min-width: 768px) and (max-width: 1023px) {
    .app-main {
        padding: var(--space-6);
    }

    .drop-zone {
        padding: var(--space-10);
    }
}
```

### Desktop (1024px+)

```css
@media (min-width: 1024px) {
    .drop-zone {
        padding: var(--space-12);
    }

    .queue-items {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    }
}
```

---

## Accessibility

### Focus Indicators

```css
*:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
    border-radius: var(--radius-sm);
}

button:focus-visible,
.file-input-label:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
}
```

### High Contrast Mode

```css
@media (prefers-contrast: high) {
    :root {
        --color-border: var(--color-neutral-900);
        --color-border-dark: var(--color-neutral-900);
    }

    .drop-zone {
        border-width: 3px;
    }

    .queue-item {
        border-width: 2px;
    }
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## Animation Guidelines

### Transitions

- **Duration**: 200ms for small UI changes, 300ms for larger animations
- **Easing**: `ease` for most transitions, `ease-out` for entrances
- **Properties**: Transform and opacity (GPU-accelerated)

### Keyframe Animations

- **Shimmer**: Progress bar loading effect (2s infinite)
- **Slide In**: Toast notification entrance (300ms once)
- **Fade In**: Queue item appearance (200ms once)

---

## CSS Architecture

### File Organization

```
src/ui/styles.css
    ├── CSS Variables (colors, typography, spacing)
    ├── Reset/Base Styles
    ├── Layout Components
    ├── Upload Components
    ├── Queue Components
    ├── Toast Components
    ├── Utilities
    ├── Responsive Overrides
    └── Accessibility Overrides
```

### Naming Conventions

- **BEM methodology**: `block__element--modifier`
- **State classes**: `--active`, `--error`, `--completed`, `--processing`
- **Utility classes**: Minimal (prefer component classes)

---

## Acceptance Tests

### CSS Validation

```bash
# W3C CSS Validator
curl -s -F "file=@src/ui/styles.css" \
  https://jigsaw.w3.org/css-validator/validator \
  -o validation-result.html

# Expected: No errors
```

### Color Contrast

```bash
# Lighthouse accessibility audit
lighthouse http://localhost:8002/ui/ \
  --only-categories=accessibility \
  --output=json \
  --output-path=accessibility-report.json

# Expected: Score >= 95
# All text must have contrast ratio >= 4.5:1 (WCAG AA)
```

### Responsive Design

```bash
# Test breakpoints
# Mobile (375px)
# Tablet (768px)
# Desktop (1200px)

# Manual testing or automated with Playwright
```

### Browser Compatibility

- **Modern browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **CSS features**: Grid, Flexbox, CSS Variables, calc()
- **Progressive enhancement**: Works without advanced features

---

## Integration Points

**Depends on**:
- `ui-html.contract.md`: HTML class names and element structure

**Provides to**:
- `upload-logic-agent`: State classes (--active, --error)
- `monitoring-logic-agent`: State classes (--processing, --completed, --failed)

---

## Implementation Notes

- Single CSS file for simplicity (no CSS modules or preprocessors)
- Use CSS variables for all design tokens
- Mobile-first responsive design
- No !important rules (except reduced-motion override)
- Comments for complex selectors only
- Ensure dark mode support (optional but recommended)
