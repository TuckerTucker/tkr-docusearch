# Accessibility Module Documentation

Comprehensive accessibility infrastructure for the Research Bot's bidirectional highlighting feature. WCAG 2.1 AA compliant.

## Overview

This module provides:
- **Keyboard Navigation**: Full keyboard control for all interactive elements
- **ARIA Labels**: Semantic labels and roles for screen readers
- **Screen Reader Announcements**: Live announcements for dynamic content
- **Accessible Animations**: Smooth, accessible highlighting effects
- **Focus Management**: Visible focus indicators and focus traps

## Modules

### 1. keyboard-nav.js

Enables comprehensive keyboard control:

```javascript
import { enableKeyboardNav } from './accessibility/keyboard-nav.js';

// Initialize keyboard navigation
enableKeyboardNav(highlighter, overlay);
```

**Keyboard Shortcuts:**
- `Tab` - Next chunk/bbox
- `Shift + Tab` - Previous chunk/bbox
- `Enter` or `Space` - Activate (permanent highlight + scroll)
- `Escape` - Clear all highlights
- `↑` `↓` - Navigate chunks in markdown
- `←` `→` - Navigate bboxes on image
- `/` - Focus search input

**Features:**
- Automatic focus management
- Keyboard mode detection (keyboard vs mouse)
- Skip links for main content
- Focus trap for modals
- No keyboard traps

### 2. aria-labels.js

Adds semantic labels for screen readers:

```javascript
import { labelBbox, labelChunk, updateHighlightState } from './accessibility/aria-labels.js';

// Label a bounding box
labelBbox(bboxElement, bboxData, index, total);

// Label a chunk
labelChunk(chunkElement, chunkData, index, total);

// Update highlight state
updateHighlightState(element, isHighlighted, isPermanent);
```

**ARIA Roles:**
- Bboxes: `role="button"` (clickable regions)
- Chunks: `role="article"` (content sections)
- Overlay: `role="img"` with descriptive label
- Indicators: `role="status"` for dynamic content

**Label Format:**
- Bboxes: `"Section: {heading}, Page {n} ({index} of {total})"`
- Chunks: `"Chunk from {section_path}, Page {n} ({index} of {total})"`
- Citations: `"Citation {n}: Reference to {document}, Page {n}"`

### 3. screen-reader-announce.js

Provides live announcements:

```javascript
import {
    announceChunkNav,
    announceHighlight,
    announceSearchResults,
    announceError
} from './accessibility/screen-reader-announce.js';

// Announce navigation
announceChunkNav('Section Heading', 2, 0, 10);

// Announce highlight
announceHighlight('chunk-1', 'section', true);

// Announce search results
announceSearchResults(5, 'query text');

// Announce error
announceError('Failed to load document');
```

**Announcement Types:**
- Navigation (polite priority)
- Highlight actions (polite priority)
- Search results (polite priority)
- Errors (assertive priority)
- Loading states (polite priority)

**ARIA Live Regions:**
- Polite region for most announcements
- Assertive region for critical announcements
- Automatic cleanup after 5 seconds

## CSS Modules

### 1. highlighting-animations.css

Smooth, accessible animations:

```css
/* Chunk highlight */
[data-chunk-id].chunk-hover {
    animation: highlightFadeIn 200ms ease-out;
}

[data-chunk-id].chunk-active {
    animation: highlightPulse 1s ease-in-out;
}

/* Bbox highlight */
.bbox-rect:hover {
    transition: all 150ms ease;
}

.bbox-rect.active {
    animation: bboxPulse 1s ease-in-out;
}
```

**Animations:**
- Fade in: 200ms ease-out
- Pulse: 1s ease-in-out
- Smooth scroll: native browser
- Reduced motion support: `@media (prefers-reduced-motion: reduce)`

### 2. accessibility.css

Core accessibility styles:

```css
/* Screen reader only */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    ...
}

/* Focus indicators */
*:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}

/* Skip links */
.skip-link {
    position: absolute;
    top: -40px;
    ...
}

.skip-link:focus {
    top: 0;
}
```

**Features:**
- Screen reader only content (`.sr-only`)
- Visible focus indicators
- Skip links for navigation
- High contrast mode support
- Keyboard navigation indicators
- Touch target sizing (44x44px minimum)

## Integration Guide

### Basic Integration

```javascript
// In details-controller.js
import { enableKeyboardNav } from './accessibility/keyboard-nav.js';
import { announceChunkNav } from './accessibility/screen-reader-announce.js';
import { labelBbox, labelChunk } from './accessibility/aria-labels.js';

class DetailsController {
    async init() {
        // Enable keyboard navigation
        enableKeyboardNav(this.highlighter, this.overlay);

        // Label elements
        this.overlay.bboxes.forEach((bbox, i) =>
            labelBbox(bbox.element, bbox, i, this.overlay.bboxes.length)
        );

        this.highlighter.chunks.forEach((chunk, i) =>
            labelChunk(chunk.element, chunk, i, this.highlighter.chunks.length)
        );
    }

    async navigateToChunk(chunkId) {
        const chunk = await this.getChunk(chunkId);
        announceChunkNav(chunk.parent_heading, chunk.page);
    }
}
```

### CSS Integration

```html
<!-- In your HTML head -->
<link rel="stylesheet" href="src/frontend/styles/accessibility.css">
<link rel="stylesheet" href="src/frontend/styles/highlighting-animations.css">
```

## WCAG 2.1 AA Compliance

### Color Contrast

✅ **Pass** - All colors meet WCAG AA requirements:
- Primary text: 7:1 contrast ratio
- Secondary text: 4.5:1 contrast ratio
- UI components: 3:1 contrast ratio

### Keyboard Accessibility

✅ **Pass** - Full keyboard operation:
- All functionality available via keyboard
- No keyboard traps
- Visible focus indicators
- Logical tab order

### Screen Reader Support

✅ **Pass** - Comprehensive screen reader support:
- All elements properly labeled
- Semantic HTML structure
- ARIA roles and attributes
- Live region announcements

### Visual Presentation

✅ **Pass** - Accessible visual design:
- Text can resize up to 200%
- Line height at least 1.5
- Paragraph spacing at least 2x font size
- No information conveyed by color alone

### Motion

✅ **Pass** - Respects motion preferences:
- `prefers-reduced-motion` support
- All animations disabled when requested
- Smooth scrolling disabled when requested

## Testing

### Manual Testing

1. **Keyboard Navigation Test**
   - Open `tests/accessibility/test-keyboard-nav.html`
   - Test all keyboard shortcuts
   - Verify focus indicators visible
   - Ensure no keyboard traps

2. **Screen Reader Test**
   - Open `tests/accessibility/test-screen-reader.html`
   - Enable VoiceOver (macOS) or NVDA (Windows)
   - Navigate through all elements
   - Verify labels and announcements

### Automated Testing

```javascript
// Run accessibility audit
npm run test:a11y

// Or use browser DevTools
// - Chrome: Lighthouse
// - Firefox: Accessibility Inspector
// - Edge: Accessibility Insights
```

### Browser Extensions

- **axe DevTools** - Comprehensive accessibility testing
- **WAVE** - Visual feedback
- **Accessibility Insights** - Microsoft's testing tool

## Best Practices

### 1. Always Label Interactive Elements

```javascript
// ❌ Bad - no label
<rect class="bbox-rect" data-bbox-id="bbox-1" />

// ✅ Good - with label
labelBbox(bboxElement, {
    element_type: 'section',
    parent_heading: 'Introduction',
    page: 1
});
```

### 2. Announce Dynamic Changes

```javascript
// ❌ Bad - silent update
highlighter.highlightChunk(chunkId);

// ✅ Good - with announcement
highlighter.highlightChunk(chunkId);
announceHighlight(chunkId, 'section', true);
```

### 3. Provide Keyboard Alternatives

```javascript
// ❌ Bad - mouse only
element.addEventListener('click', handler);

// ✅ Good - keyboard support
element.addEventListener('click', handler);
element.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handler();
    }
});
```

### 4. Update ARIA States

```javascript
// ❌ Bad - state not updated
element.classList.add('active');

// ✅ Good - ARIA state updated
element.classList.add('active');
updateHighlightState(element, true, true);
```

### 5. Focus Management

```javascript
// ❌ Bad - focus lost
modal.classList.add('hidden');

// ✅ Good - focus restored
const restoreFocus = saveFocus();
modal.classList.add('hidden');
restoreFocus();
```

## Common Issues and Solutions

### Issue: Focus indicators not visible

**Solution:** Ensure CSS is loaded and `:focus-visible` is supported:

```css
*:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}
```

### Issue: Screen reader not announcing changes

**Solution:** Verify live regions are initialized:

```javascript
import { initializeLiveRegions } from './screen-reader-announce.js';
initializeLiveRegions();
```

### Issue: Keyboard trap in modal

**Solution:** Use `trapFocus` helper:

```javascript
import { trapFocus } from './keyboard-nav.js';
trapFocus(modalElement);
```

### Issue: Skip links not working

**Solution:** Ensure targets have `id` attributes:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
...
<main id="main-content">...</main>
```

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Dependencies

None. Pure vanilla JavaScript and CSS.

## File Structure

```
src/frontend/accessibility/
├── keyboard-nav.js           (~300 lines)
├── aria-labels.js            (~200 lines)
├── screen-reader-announce.js (~150 lines)
└── README.md

src/frontend/styles/
├── accessibility.css         (~200 lines)
└── highlighting-animations.css (~150 lines)

tests/accessibility/
├── test-keyboard-nav.html    (~200 lines)
└── test-screen-reader.html   (~200 lines)
```

## Performance

- **No runtime overhead** - Event listeners only on interactive elements
- **Minimal DOM manipulation** - Live regions reused
- **CSS animations** - GPU accelerated
- **Lazy initialization** - Live regions created on first use

## Future Enhancements

- [ ] Voice control support (Dragon NaturallySpeaking)
- [ ] Switch device support
- [ ] Eye tracking support
- [ ] Braille display optimization
- [ ] Internationalization (i18n) for announcements

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [WebAIM Resources](https://webaim.org/resources/)

## Support

For issues or questions:
1. Check the test pages for examples
2. Review the integration guide
3. Consult the best practices section
4. Open an issue with reproduction steps
