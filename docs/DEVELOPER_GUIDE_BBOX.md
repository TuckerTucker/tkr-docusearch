# Developer Guide: Bounding Box Coordinates

**Version:** 1.0
**Last Updated:** 2025-10-17
**Audience:** Developers implementing document structure features

---

## Critical: Y-Axis Flip Required ⚠️

**The #1 mistake when working with bounding boxes is forgetting the Y-axis flip.**

PDF documents use a **bottom-left origin** with Y increasing upward ↑, while screens use **top-left origin** with Y increasing downward ↓.

**You MUST transform coordinates when rendering bboxes on screen.**

---

## Table of Contents

1. [Coordinate Systems](#coordinate-systems)
2. [Transformation Formulas](#transformation-formulas)
3. [Step-by-Step Examples](#step-by-step-examples)
4. [Common Mistakes](#common-mistakes)
5. [Code Examples](#code-examples)
6. [Testing Bounding Boxes](#testing-bounding-boxes)
7. [Visual Diagrams](#visual-diagrams)
8. [FAQ](#faq)

---

## Coordinate Systems

### PDF Coordinate System

**Origin:** Bottom-left corner (0, 0)
**X-Axis:** Left to right →
**Y-Axis:** Bottom to top ↑
**Units:** Points (1 point = 1/72 inch)

```
Standard Letter Page: 612pt × 792pt

        ┌─────────────────────────┐ (612, 792) Top-right
        │                         │
        │                         │  ↑
        │                         │  │ Y increases upward
        │                         │  │
        │                         │
(0,0) ──┴─────────────────────────┘
     Bottom-left                    X increases rightward →
```

**Bounding Box Format:**

```python
bbox = {
    'left': 72,      # Distance from left edge
    'bottom': 650,   # Distance from bottom edge (LOWER Y value)
    'right': 540,    # Distance from left edge
    'top': 720       # Distance from bottom edge (HIGHER Y value)
}

# Note: bottom < top (because Y increases upward)
```

### Screen Coordinate System

**Origin:** Top-left corner (0, 0)
**X-Axis:** Left to right →
**Y-Axis:** Top to bottom ↓
**Units:** Pixels

```
Browser Canvas: 816px × 1056px

(0,0) ┬─────────────────────────┐ Top-left
      │                         │
      │                         │  ↓
      │                         │  │ Y increases downward
      │                         │  │
      │                         │
      └─────────────────────────┘ (816, 1056) Bottom-right
                                   X increases rightward →
```

**Bounding Box Format:**

```javascript
bbox = {
    x: 96,          // Distance from left edge
    y: 336,         // Distance from top edge (smaller = higher up)
    width: 624,     // Horizontal span
    height: 93      // Vertical span
}

// Note: y=0 is at TOP, not bottom
```

### Key Differences

| Property | PDF | Screen |
|----------|-----|--------|
| **Origin** | Bottom-left | Top-left |
| **Y=0 Position** | Bottom edge | Top edge |
| **Y Direction** | Upward ↑ | Downward ↓ |
| **Units** | Points (pt) | Pixels (px) |
| **Bbox Format** | `{left, bottom, right, top}` | `{x, y, width, height}` |

---

## Transformation Formulas

### PDF → Screen (JavaScript)

```javascript
/**
 * Transform PDF bounding box to screen coordinates.
 *
 * @param {Object} pdfBbox - PDF bbox {left, bottom, right, top} in points
 * @param {number} pdfWidth - PDF page width in points
 * @param {number} pdfHeight - PDF page height in points
 * @param {number} screenWidth - Screen width in pixels
 * @param {number} screenHeight - Screen height in pixels
 * @returns {Object} Screen bbox {x, y, width, height} in pixels
 */
function transformPdfToScreen(pdfBbox, pdfWidth, pdfHeight, screenWidth, screenHeight) {
    // Calculate scale factors
    const scaleX = screenWidth / pdfWidth;
    const scaleY = screenHeight / pdfHeight;

    // Transform coordinates
    return {
        x: pdfBbox.left * scaleX,
        y: screenHeight - (pdfBbox.top * scaleY),  // ← Y-AXIS FLIP!
        width: (pdfBbox.right - pdfBbox.left) * scaleX,
        height: (pdfBbox.top - pdfBbox.bottom) * scaleY
    };
}
```

**Formula Breakdown:**

```javascript
// X coordinate (same direction)
screen.x = pdf.left × (screenWidth / pdfWidth)

// Y coordinate (INVERTED direction)
screen.y = screenHeight - (pdf.top × (screenHeight / pdfHeight))
//         ↑              ↑
//         Total height   Flip by subtracting from total height

// Width (proportional scaling)
screen.width = (pdf.right - pdf.left) × (screenWidth / pdfWidth)

// Height (proportional scaling)
screen.height = (pdf.top - pdf.bottom) × (screenHeight / pdfHeight)
```

### Screen → PDF (JavaScript)

```javascript
/**
 * Transform screen coordinates back to PDF bbox.
 *
 * @param {Object} screenBbox - Screen bbox {x, y, width, height} in pixels
 * @param {number} pdfWidth - PDF page width in points
 * @param {number} pdfHeight - PDF page height in points
 * @param {number} screenWidth - Screen width in pixels
 * @param {number} screenHeight - Screen height in pixels
 * @returns {Object} PDF bbox {left, bottom, right, top} in points
 */
function transformScreenToPdf(screenBbox, pdfWidth, pdfHeight, screenWidth, screenHeight) {
    // Calculate scale factors
    const scaleX = pdfWidth / screenWidth;
    const scaleY = pdfHeight / screenHeight;

    // Transform coordinates (inverse of PDF → Screen)
    const left = screenBbox.x * scaleX;
    const top = (screenHeight - screenBbox.y) * scaleY;  // ← Y-AXIS FLIP!
    const right = (screenBbox.x + screenBbox.width) * scaleX;
    const bottom = (screenHeight - (screenBbox.y + screenBbox.height)) * scaleY;

    return { left, bottom, right, top };
}
```

### Python Implementation

```python
from typing import Dict, Tuple

def transform_pdf_to_screen(
    pdf_bbox: Dict[str, float],
    pdf_width: float,
    pdf_height: float,
    screen_width: float,
    screen_height: float
) -> Dict[str, float]:
    """Transform PDF bbox to screen coordinates."""
    scale_x = screen_width / pdf_width
    scale_y = screen_height / pdf_height

    return {
        'x': pdf_bbox['left'] * scale_x,
        'y': screen_height - (pdf_bbox['top'] * scale_y),  # Y-AXIS FLIP!
        'width': (pdf_bbox['right'] - pdf_bbox['left']) * scale_x,
        'height': (pdf_bbox['top'] - pdf_bbox['bottom']) * scale_y
    }

def transform_screen_to_pdf(
    screen_bbox: Dict[str, float],
    pdf_width: float,
    pdf_height: float,
    screen_width: float,
    screen_height: float
) -> Dict[str, float]:
    """Transform screen bbox to PDF coordinates."""
    scale_x = pdf_width / screen_width
    scale_y = pdf_height / screen_height

    left = screen_bbox['x'] * scale_x
    top = (screen_height - screen_bbox['y']) * scale_y  # Y-AXIS FLIP!
    right = (screen_bbox['x'] + screen_bbox['width']) * scale_x
    bottom = (screen_height - (screen_bbox['y'] + screen_bbox['height'])) * scale_y

    return {
        'left': left,
        'bottom': bottom,
        'right': right,
        'top': top
    }
```

---

## Step-by-Step Examples

### Example 1: Heading at Top of Page

**Scenario:** Transform a heading bounding box at the top of a PDF page.

**Given:**
- PDF page: 612pt × 792pt (standard letter)
- Screen image: 816px × 1056px
- Heading bbox in PDF coordinates:
  ```python
  pdf_bbox = {
      'left': 72,      # 1 inch from left
      'bottom': 720,   # Near top of page
      'right': 540,    # 7.5 inches from left
      'top': 750       # At top of page
  }
  ```

**Step 1: Calculate scale factors**
```python
scale_x = 816 / 612 = 1.333...
scale_y = 1056 / 792 = 1.333...
```

**Step 2: Transform X coordinate (no flip)**
```python
screen_x = pdf_left × scale_x
         = 72 × 1.333
         = 96 pixels
```

**Step 3: Transform Y coordinate (WITH flip)**
```python
screen_y = screen_height - (pdf_top × scale_y)
         = 1056 - (750 × 1.333)
         = 1056 - 1000
         = 56 pixels  ← Near TOP of screen (small Y value)
```

**Step 4: Calculate width**
```python
screen_width = (pdf_right - pdf_left) × scale_x
             = (540 - 72) × 1.333
             = 468 × 1.333
             = 624 pixels
```

**Step 5: Calculate height**
```python
screen_height = (pdf_top - pdf_bottom) × scale_y
              = (750 - 720) × 1.333
              = 30 × 1.333
              = 40 pixels
```

**Result:**
```javascript
screen_bbox = {
    x: 96,       // 96 pixels from left
    y: 56,       // 56 pixels from TOP (heading is near top)
    width: 624,  // 624 pixels wide
    height: 40   // 40 pixels tall
}
```

**Visual:**
```
Screen (816px × 1056px):

(0,0) ┬─────────────────────────────────┐
      │                                 │
      │  ┌─────────────────────┐ ← 56px from top
      │  │   HEADING BBOX      │
      │  └─────────────────────┘
      │        96px ↑  624px wide
      │                                 │
      │                                 │
      └─────────────────────────────────┘
```

### Example 2: Paragraph at Bottom of Page

**Given:**
- Same page dimensions (612pt × 792pt → 816px × 1056px)
- Paragraph bbox in PDF coordinates:
  ```python
  pdf_bbox = {
      'left': 72,
      'bottom': 50,    # Near bottom of page
      'right': 540,
      'top': 100       # Slightly higher
  }
  ```

**Step 1-2: Scale factors (same as before)**
```python
scale_x = 1.333
scale_y = 1.333
```

**Step 3: Transform Y coordinate**
```python
screen_y = 1056 - (100 × 1.333)
         = 1056 - 133
         = 923 pixels  ← Near BOTTOM of screen (large Y value)
```

**Step 4-5: Width and height**
```python
screen_width = (540 - 72) × 1.333 = 624 pixels
screen_height = (100 - 50) × 1.333 = 67 pixels
```

**Result:**
```javascript
screen_bbox = {
    x: 96,
    y: 923,      // 923 pixels from top = near bottom
    width: 624,
    height: 67
}
```

**Visual:**
```
Screen (816px × 1056px):

(0,0) ┬─────────────────────────────────┐
      │                                 │
      │                                 │
      │                                 │
      │                                 │
      │  ┌─────────────────────┐ ← 923px from top
      │  │  PARAGRAPH BBOX     │
      │  └─────────────────────┘
      └─────────────────────────────────┘ (1056px)
```

### Example 3: Table in Middle of Page

**Given:**
- PDF page: 612pt × 792pt
- Screen: 816px × 1056px
- Table bbox:
  ```python
  pdf_bbox = {
      'left': 72,
      'bottom': 300,   # Middle of page
      'right': 540,
      'top': 500       # Middle of page
  }
  ```

**Transform:**
```python
screen_y = 1056 - (500 × 1.333)
         = 1056 - 667
         = 389 pixels  ← MIDDLE of screen

screen_height = (500 - 300) × 1.333
              = 200 × 1.333
              = 267 pixels
```

**Result:**
```javascript
screen_bbox = {
    x: 96,
    y: 389,      // Middle of screen
    width: 624,
    height: 267  // Tall table
}
```

---

## Common Mistakes

### Mistake #1: Forgetting Y-Axis Flip

**❌ WRONG:**
```javascript
// Directly using PDF Y coordinate on screen
screen_y = pdf_bbox.top * scale_y;  // NO! This is upside-down!
```

**✅ CORRECT:**
```javascript
// Flip Y-axis by subtracting from total height
screen_y = screenHeight - (pdf_bbox.top * scale_y);
```

**Why it matters:**
- Without flip: Heading at top of PDF appears at bottom of screen
- With flip: Heading at top of PDF correctly appears at top of screen

### Mistake #2: Using `bottom` Instead of `top` for Y

**❌ WRONG:**
```javascript
screen_y = screenHeight - (pdf_bbox.bottom * scale_y);  // NO!
```

**✅ CORRECT:**
```javascript
screen_y = screenHeight - (pdf_bbox.top * scale_y);
```

**Why it matters:**
- `bottom` is the LOWER edge (smaller Y value in PDF)
- `top` is the UPPER edge (larger Y value in PDF)
- Screen Y should be measured from the TOP edge

### Mistake #3: Swapping Width/Height Calculation

**❌ WRONG:**
```javascript
width = pdf_bbox.top - pdf_bbox.bottom;  // NO! This is height!
height = pdf_bbox.right - pdf_bbox.left;  // NO! This is width!
```

**✅ CORRECT:**
```javascript
width = pdf_bbox.right - pdf_bbox.left;
height = pdf_bbox.top - pdf_bbox.bottom;
```

### Mistake #4: Forgetting to Scale

**❌ WRONG:**
```javascript
// Using PDF coordinates directly on screen
screen_x = pdf_bbox.left;  // NO! PDF is 612pt, screen might be 816px!
```

**✅ CORRECT:**
```javascript
screen_x = pdf_bbox.left * (screenWidth / pdfWidth);
```

### Mistake #5: Using Pixel Units in PDF

**❌ WRONG:**
```python
# Assuming PDF uses pixels
pdf_width = 1200  # NO! PDF uses points, not pixels!
```

**✅ CORRECT:**
```python
# Standard PDF page sizes in POINTS
pdf_width = 612   # Letter width in points
pdf_height = 792  # Letter height in points
```

### Mistake #6: Incorrect Bbox Ordering

**❌ WRONG:**
```python
pdf_bbox = {
    'left': 72,
    'bottom': 720,   # NO! bottom should be < top
    'right': 540,
    'top': 650       # NO! top should be > bottom
}
```

**✅ CORRECT:**
```python
pdf_bbox = {
    'left': 72,
    'bottom': 650,   # Lower edge (smaller Y)
    'right': 540,
    'top': 720       # Upper edge (larger Y)
}
```

**Validation:**
```python
assert bbox['bottom'] < bbox['top'], "bottom must be < top"
assert bbox['left'] < bbox['right'], "left must be < right"
```

---

## Code Examples

### Complete Implementation (JavaScript)

```javascript
/**
 * Comprehensive bounding box transformation utilities.
 */
class BboxTransformer {
    constructor(pdfWidth, pdfHeight, screenWidth, screenHeight) {
        this.pdfWidth = pdfWidth;
        this.pdfHeight = pdfHeight;
        this.screenWidth = screenWidth;
        this.screenHeight = screenHeight;
        this.scaleX = screenWidth / pdfWidth;
        this.scaleY = screenHeight / pdfHeight;
    }

    /**
     * Transform PDF bbox to screen coordinates.
     */
    pdfToScreen(pdfBbox) {
        return {
            x: pdfBbox.left * this.scaleX,
            y: this.screenHeight - (pdfBbox.top * this.scaleY),  // Y-FLIP
            width: (pdfBbox.right - pdfBbox.left) * this.scaleX,
            height: (pdfBbox.top - pdfBbox.bottom) * this.scaleY
        };
    }

    /**
     * Transform screen bbox to PDF coordinates.
     */
    screenToPdf(screenBbox) {
        return {
            left: screenBbox.x / this.scaleX,
            bottom: (this.screenHeight - (screenBbox.y + screenBbox.height)) / this.scaleY,
            right: (screenBbox.x + screenBbox.width) / this.scaleX,
            top: (this.screenHeight - screenBbox.y) / this.scaleY
        };
    }

    /**
     * Validate PDF bbox format.
     */
    validatePdfBbox(bbox) {
        if (bbox.left >= bbox.right) {
            throw new Error(`Invalid PDF bbox: left >= right (${bbox.left} >= ${bbox.right})`);
        }
        if (bbox.bottom >= bbox.top) {
            throw new Error(`Invalid PDF bbox: bottom >= top (${bbox.bottom} >= ${bbox.top})`);
        }
        if (bbox.left < 0 || bbox.right > this.pdfWidth) {
            throw new Error(`PDF bbox out of horizontal bounds: ${JSON.stringify(bbox)}`);
        }
        if (bbox.bottom < 0 || bbox.top > this.pdfHeight) {
            throw new Error(`PDF bbox out of vertical bounds: ${JSON.stringify(bbox)}`);
        }
        return true;
    }

    /**
     * Validate screen bbox format.
     */
    validateScreenBbox(bbox) {
        if (bbox.width <= 0 || bbox.height <= 0) {
            throw new Error(`Invalid screen bbox: non-positive dimensions`);
        }
        if (bbox.x < 0 || bbox.x + bbox.width > this.screenWidth) {
            throw new Error(`Screen bbox out of horizontal bounds`);
        }
        if (bbox.y < 0 || bbox.y + bbox.height > this.screenHeight) {
            throw new Error(`Screen bbox out of vertical bounds`);
        }
        return true;
    }
}

// Usage
const transformer = new BboxTransformer(
    612,   // PDF width (Letter)
    792,   // PDF height (Letter)
    816,   // Screen width
    1056   // Screen height
);

const pdfBbox = { left: 72, bottom: 650, right: 540, top: 720 };
transformer.validatePdfBbox(pdfBbox);
const screenBbox = transformer.pdfToScreen(pdfBbox);
console.log(screenBbox);
// { x: 96, y: 336, width: 624, height: 93 }
```

### SVG Rendering Example

```javascript
/**
 * Render bounding boxes as SVG overlay.
 */
function renderBboxOverlay(structure, pageImageElement) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', pageImageElement.width);
    svg.setAttribute('height', pageImageElement.height);
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.pointerEvents = 'auto';

    const transformer = new BboxTransformer(
        structure.page_width,
        structure.page_height,
        pageImageElement.width,
        pageImageElement.height
    );

    structure.elements.forEach(element => {
        // Transform PDF bbox to screen
        const screenBbox = transformer.pdfToScreen(element.bbox);

        // Create SVG rectangle
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', screenBbox.x);
        rect.setAttribute('y', screenBbox.y);
        rect.setAttribute('width', screenBbox.width);
        rect.setAttribute('height', screenBbox.height);
        rect.setAttribute('data-element-id', element.id);
        rect.setAttribute('data-chunk-id', element.chunk_id);
        rect.classList.add('bbox-region', `bbox-${element.type}`);

        // Style based on element type
        rect.style.stroke = getBboxColor(element.type);
        rect.style.strokeWidth = '2px';
        rect.style.fill = 'none';
        rect.style.cursor = 'pointer';

        svg.appendChild(rect);
    });

    pageImageElement.parentElement.appendChild(svg);
}

function getBboxColor(elementType) {
    const colors = {
        'heading': 'blue',
        'paragraph': 'green',
        'list': 'orange',
        'table': 'purple',
        'figure': 'red'
    };
    return colors[elementType] || 'gray';
}
```

### Python Validation Example

```python
"""Bounding box validation utilities."""

from typing import Dict, Tuple

class BboxValidator:
    """Validate bounding box coordinates."""

    def __init__(self, page_width: float, page_height: float):
        self.page_width = page_width
        self.page_height = page_height

    def validate_pdf_bbox(self, bbox: Dict[str, float]) -> Tuple[bool, str]:
        """
        Validate PDF bounding box.

        Returns:
            (is_valid, error_message)
        """
        # Check ordering
        if bbox['left'] >= bbox['right']:
            return False, f"left >= right ({bbox['left']} >= {bbox['right']})"

        if bbox['bottom'] >= bbox['top']:
            return False, f"bottom >= top ({bbox['bottom']} >= {bbox['top']})"

        # Check bounds
        if bbox['left'] < 0 or bbox['right'] > self.page_width:
            return False, f"Bbox out of horizontal bounds: {bbox}"

        if bbox['bottom'] < 0 or bbox['top'] > self.page_height:
            return False, f"Bbox out of vertical bounds: {bbox}"

        return True, ""

    def validate_transformation(
        self,
        pdf_bbox: Dict[str, float],
        screen_bbox: Dict[str, float],
        screen_width: float,
        screen_height: float,
        tolerance: float = 1.0
    ) -> bool:
        """
        Validate that transformation is correct.

        Args:
            tolerance: Allowed error in pixels (default 1.0)
        """
        scale_x = screen_width / self.page_width
        scale_y = screen_height / self.page_height

        # Check X transformation
        expected_x = pdf_bbox['left'] * scale_x
        if abs(screen_bbox['x'] - expected_x) > tolerance:
            return False

        # Check Y transformation (with flip)
        expected_y = screen_height - (pdf_bbox['top'] * scale_y)
        if abs(screen_bbox['y'] - expected_y) > tolerance:
            return False

        # Check width
        expected_width = (pdf_bbox['right'] - pdf_bbox['left']) * scale_x
        if abs(screen_bbox['width'] - expected_width) > tolerance:
            return False

        # Check height
        expected_height = (pdf_bbox['top'] - pdf_bbox['bottom']) * scale_y
        if abs(screen_bbox['height'] - expected_height) > tolerance:
            return False

        return True

# Usage
validator = BboxValidator(page_width=612, page_height=792)

pdf_bbox = {'left': 72, 'bottom': 650, 'right': 540, 'top': 720}
is_valid, error = validator.validate_pdf_bbox(pdf_bbox)

if not is_valid:
    print(f"Invalid bbox: {error}")
else:
    print("Bbox is valid")
```

---

## Testing Bounding Boxes

### Unit Tests (JavaScript)

```javascript
describe('BboxTransformer', () => {
    const transformer = new BboxTransformer(612, 792, 816, 1056);

    test('transforms heading at top of page correctly', () => {
        const pdfBbox = { left: 72, bottom: 720, right: 540, top: 750 };
        const screenBbox = transformer.pdfToScreen(pdfBbox);

        expect(screenBbox.x).toBeCloseTo(96, 1);
        expect(screenBbox.y).toBeCloseTo(56, 1);  // Near top (small Y)
        expect(screenBbox.width).toBeCloseTo(624, 1);
        expect(screenBbox.height).toBeCloseTo(40, 1);
    });

    test('transforms paragraph at bottom correctly', () => {
        const pdfBbox = { left: 72, bottom: 50, right: 540, top: 100 };
        const screenBbox = transformer.pdfToScreen(pdfBbox);

        expect(screenBbox.y).toBeCloseTo(923, 1);  // Near bottom (large Y)
    });

    test('round-trip transformation preserves bbox', () => {
        const original = { left: 72, bottom: 300, right: 540, top: 500 };
        const screen = transformer.pdfToScreen(original);
        const restored = transformer.screenToPdf(screen);

        expect(restored.left).toBeCloseTo(original.left, 1);
        expect(restored.bottom).toBeCloseTo(original.bottom, 1);
        expect(restored.right).toBeCloseTo(original.right, 1);
        expect(restored.top).toBeCloseTo(original.top, 1);
    });

    test('validates bbox ordering', () => {
        expect(() => {
            transformer.validatePdfBbox({ left: 540, bottom: 650, right: 72, top: 720 });
        }).toThrow('left >= right');

        expect(() => {
            transformer.validatePdfBbox({ left: 72, bottom: 720, right: 540, top: 650 });
        }).toThrow('bottom >= top');
    });
});
```

### Visual Regression Tests (Python)

```python
"""Visual regression tests for bbox rendering."""

import pytest
from playwright.sync_api import Page

def test_bbox_alignment(page: Page):
    """Verify bboxes visually align with content."""
    # Navigate to document page
    page.goto('http://localhost:8000/documents/test_doc')

    # Take screenshot
    screenshot = page.screenshot()

    # Compare with baseline
    assert_screenshots_match(screenshot, 'baseline_bbox_alignment.png')

def test_bbox_hover_highlighting(page: Page):
    """Verify hover highlights correct region."""
    page.goto('http://localhost:8000/documents/test_doc')

    # Hover over first chunk
    page.hover('[data-chunk-id="chunk_0"]')

    # Check bbox is highlighted
    bbox = page.locator('[data-element-id="elem_0"]')
    assert 'bbox-highlighted' in bbox.get_attribute('class')

def test_bbox_click_navigation(page: Page):
    """Verify clicking bbox scrolls to chunk."""
    page.goto('http://localhost:8000/documents/test_doc')

    # Click bbox
    page.click('[data-element-id="elem_5"]')

    # Verify chunk is in viewport
    chunk = page.locator('[data-chunk-id="chunk_5"]')
    assert chunk.is_visible()
```

---

## Visual Diagrams

### Y-Axis Flip Visualization

```
PDF Coordinate System (Origin: Bottom-Left)

        ┌─────────────────┐ top=720 (higher Y value)
        │                 │
        │   HEADING       │  ↑
        │                 │  │ Y increases upward
        └─────────────────┘ bottom=650 (lower Y value)

                ↓ TRANSFORMATION ↓
              (flip Y-axis)

Screen Coordinate System (Origin: Top-Left)

        ┌─────────────────┐ y=336 (distance from top)
        │                 │
        │   HEADING       │  ↓
        │                 │  │ Y increases downward
        └─────────────────┘ y+height=376

Formula: screen_y = screen_height - (pdf_top × scale_y)
         336 = 1056 - (720 × 1.333)
```

### Multi-Element Example

```
PDF Page (612pt × 792pt):

      0 ┌─────────────────────────────────┐ 792
        │  ┌───────────────┐ top=750      │ ↑
        │  │   HEADING     │ bottom=720   │ │
        │  └───────────────┘               │ │
        │                                  │ │
        │  ┌───────────────────────┐       │ │ Y
        │  │                       │ top=500│ │
        │  │      TABLE            │       │ │
        │  │                       │       │ │
        │  └───────────────────────┘ bottom=300 │
        │                                  │ │
        │  ┌───────────────┐ top=100      │ │
        │  │  PARAGRAPH    │ bottom=50    │ │
        └──┴───────────────┴──────────────┘ 0
           72              540 (X →)

                ↓ TRANSFORM ↓

Screen (816px × 1056px):

    0,0 ┌─────────────────────────────────┐
        │  ┌───────────────┐ y=56         │ ↓
        │  │   HEADING     │ height=40    │ │
        │  └───────────────┘               │ │
        │                                  │ │
        │  ┌───────────────────────┐       │ │ Y
        │  │                       │ y=389 │ │
        │  │      TABLE            │       │ │
        │  │                       │ height=267│
        │  └───────────────────────┘       │ │
        │                                  │ │
        │  ┌───────────────┐ y=923        │ │
        │  │  PARAGRAPH    │ height=67    │ │
        └──┴───────────────┴──────────────┘ 1056
           96 (X →)         720
```

---

## FAQ

### Q: Why does PDF use bottom-left origin?

**A:** Historical reasons. PostScript (PDF's predecessor) was designed for printers, which feed paper from the bottom. The coordinate system reflects physical paper handling.

### Q: Do all PDFs use the same coordinate system?

**A:** Yes, the PDF specification mandates bottom-left origin. However, page sizes vary (Letter, A4, etc.).

### Q: What if the PDF page is rotated?

**A:** Rotation complicates things. You may need to:
1. Detect rotation (0°, 90°, 180°, 270°)
2. Apply rotation transformation in addition to Y-flip
3. Adjust page width/height for 90°/270° rotations

```javascript
// Pseudo-code for rotated pages
if (rotation === 90) {
    // Swap width/height and adjust coordinates
    screenBbox = transformRotated90(pdfBbox, ...);
}
```

### Q: How do I handle non-uniform scaling?

**A:** If the screen aspect ratio differs from PDF, you have two options:

**Option 1: Uniform scaling (letterbox/pillarbox)**
```javascript
const scale = Math.min(screenWidth / pdfWidth, screenHeight / pdfHeight);
const scaleX = scale;
const scaleY = scale;
// Bboxes remain proportional, but image may have black bars
```

**Option 2: Non-uniform scaling (stretch)**
```javascript
const scaleX = screenWidth / pdfWidth;
const scaleY = screenHeight / pdfHeight;
// Bboxes may appear distorted if scaleX ≠ scaleY
```

**Recommendation:** Use uniform scaling to preserve bbox proportions.

### Q: What precision should I use for coordinates?

**A:** 1 decimal place is usually sufficient:

```javascript
Math.round(screenBbox.x * 10) / 10  // Round to 0.1 pixel
```

### Q: How do I debug bbox alignment issues?

**A:**
1. **Log transformed coordinates:**
   ```javascript
   console.log('PDF:', pdfBbox);
   console.log('Screen:', screenBbox);
   ```

2. **Render bboxes with high opacity:**
   ```css
   .bbox-region {
       fill: rgba(255, 0, 0, 0.3);  /* Visible red fill */
   }
   ```

3. **Check scale factors:**
   ```javascript
   console.log('scaleX:', scaleX, 'scaleY:', scaleY);
   // Should be equal for uniform scaling
   ```

4. **Validate transformation:**
   ```javascript
   const restored = transformer.screenToPdf(screenBbox);
   console.assert(Math.abs(restored.left - pdfBbox.left) < 1);
   ```

### Q: What about multi-column layouts?

**A:** Bboxes work the same way. Each column has its own bboxes:

```python
# Column 1 (left)
bbox1 = {'left': 72, 'bottom': 100, 'right': 270, 'top': 700}

# Column 2 (right)
bbox2 = {'left': 342, 'bottom': 100, 'right': 540, 'top': 700}
```

Both transform independently using the same formula.

---

## Additional Resources

- **[Enhanced Mode User Guide](ENHANCED_MODE.md)** - User-facing documentation
- **[Bidirectional Highlighting Guide](BIDIRECTIONAL_HIGHLIGHTING.md)** - System architecture
- **[API Reference](API_ENHANCED_ENDPOINTS.md)** - Complete API documentation
- **[PDF Reference](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf)** - Official PDF specification
- **[SVG Specification](https://www.w3.org/TR/SVG2/)** - SVG rendering details

---

**Master the Y-flip, and bounding boxes will never confuse you again! 🎯**
