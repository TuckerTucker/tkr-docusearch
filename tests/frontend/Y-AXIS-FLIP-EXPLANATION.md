# Y-Axis Flip Explanation

**Critical concept for understanding BoundingBox Overlay coordinate transformation**

---

## The Problem

PDF documents use a **bottom-left origin** coordinate system (inherited from PostScript), while web browsers use a **top-left origin** for images and SVG. This means Y-coordinates are inverted.

---

## Visual Comparison

### PDF Coordinate System (Input)

```
Y-axis (points)
↑ 792 pt (top of US Letter page)
│
│ ┌─────────────────┐
│ │  PDF TOP = 720  │ ← High Y value
│ │   (Heading)     │
│ ├─────────────────┤
│ │                 │
│ │    Content      │
│ │                 │
│ ├─────────────────┤
│ │ PDF BOTTOM=100  │ ← Low Y value
│ │   (Picture)     │
│ └─────────────────┘
│
0 pt (bottom of page) ────────────> X-axis (points)
                              612 pt (right edge)

Origin: Bottom-left corner (0, 0)
Y increases: Upward ↑
Bbox format: {left, bottom, right, top}
```

### Screen Coordinate System (Output)

```
0 px (top of image) ────────────> X-axis (pixels)
│                            1020 px (right edge)
│ ┌─────────────────┐
│ │ SCREEN TOP = 120│ ← Low Y value (was PDF top)
│ │   (Heading)     │
│ ├─────────────────┤
│ │                 │
│ │    Content      │
│ │                 │
│ ├─────────────────┤
│ │SCREEN TOP = 820 │ ← High Y value (was PDF bottom)
│ │   (Picture)     │
│ └─────────────────┘
↓
1320 px (bottom of image)
Y-axis (pixels)

Origin: Top-left corner (0, 0)
Y increases: Downward ↓
Bbox format: {x, y, width, height}
```

---

## The Flip

Notice what happens:

| Element | PDF Y-coords | PDF Position | Screen Y-coord | Screen Position |
|---------|--------------|--------------|----------------|-----------------|
| Heading | bottom=650, top=720 | **Near TOP** (high Y) | y=120 | **Near TOP** (low Y) ✅ |
| Picture | bottom=100, top=300 | **Near BOTTOM** (low Y) | y=820 | **Near BOTTOM** (high Y) ✅ |

**Key insight:**
- PDF: Top of page = **high Y values** (e.g., 720)
- Screen: Top of image = **low Y values** (e.g., 120)

Therefore, we need to **flip the Y-axis** during transformation.

---

## Transformation Formula

### Step 1: Calculate Scale Factors

```javascript
// Example: 150 DPI rendering
pdfWidth = 612 points
pdfHeight = 792 points
imageWidth = 1020 pixels  // 612 * (150/72) ≈ 1275
imageHeight = 1320 pixels // 792 * (150/72) ≈ 1650

scaleX = imageWidth / pdfWidth   // 1020 / 612 = 1.667
scaleY = imageHeight / pdfHeight // 1320 / 792 = 1.667
```

### Step 2: Transform Coordinates with Y-Flip

```javascript
// Example: Heading bbox
pdfBbox = {
  left: 72,    // Left edge
  bottom: 650, // Bottom edge (lower Y in PDF)
  right: 540,  // Right edge
  top: 720     // Top edge (higher Y in PDF)
}

// X coordinates (no flip needed)
screenLeft = pdfBbox.left * scaleX
           = 72 * 1.667
           = 120 pixels

screenRight = pdfBbox.right * scaleX
            = 540 * 1.667
            = 900 pixels

// Y coordinates (FLIP REQUIRED!)
// The trick: subtract from imageHeight to flip origin
screenTop = imageHeight - (pdfBbox.top * scaleY)
          = 1320 - (720 * 1.667)
          = 1320 - 1200
          = 120 pixels  ← Near top of image!

screenBottom = imageHeight - (pdfBbox.bottom * scaleY)
             = 1320 - (650 * 1.667)
             = 1320 - 1083.33
             = 236.67 pixels

// Final screen bbox
screenBbox = {
  x: 120,           // Left edge (same as PDF left)
  y: 120,           // Top edge (flipped!)
  width: 780,       // 900 - 120
  height: 116.67    // 236.67 - 120
}
```

### Step 3: Verification

```javascript
// Verify Y-flip is correct:
// PDF top (720) is at 720/792 = 91% from bottom
// Screen top (120) is at 120/1320 = 9% from top
// 91% from bottom = 9% from top ✅ CORRECT!

// PDF center:
pdfCenterY = (pdfBbox.bottom + pdfBbox.top) / 2
           = (650 + 720) / 2
           = 685  // 685/792 = 86% from bottom

// Screen center:
screenCenterY = screenBbox.y + (screenBbox.height / 2)
              = 120 + 58.33
              = 178.33  // 178.33/1320 = 13.5% from top

// 86% from bottom ≈ 14% from top ✅ CORRECT!
```

---

## Why This Matters

**Without Y-flip:**
- Heading at PDF top (Y=720) would appear at screen bottom
- Picture at PDF bottom (Y=100) would appear at screen top
- **Everything would be upside-down! ❌**

**With Y-flip:**
- Heading at PDF top (Y=720) appears at screen top (y=120)
- Picture at PDF bottom (Y=100) appears at screen bottom (y=820)
- **Correct positioning! ✅**

---

## Code Implementation

### Incorrect (No Flip)

```javascript
// ❌ WRONG - This produces upside-down bboxes
screenTop = pdfBbox.top * scaleY        // Would be 1200
screenBottom = pdfBbox.bottom * scaleY  // Would be 1083.33

// Result: Top > Bottom (invalid!)
```

### Correct (With Flip)

```javascript
// ✅ CORRECT - Flip Y-axis by subtracting from imageHeight
screenTop = imageHeight - (pdfBbox.top * scaleY)
screenBottom = imageHeight - (pdfBbox.bottom * scaleY)

// Result: Top < Bottom (valid!)
```

---

## Real-World Example

### Input (from Structure API)

```json
{
  "headings": [
    {
      "text": "Introduction to Machine Learning",
      "bbox": {
        "left": 72.0,
        "bottom": 650.0,
        "right": 540.0,
        "top": 720.0
      }
    }
  ]
}
```

### Transformation

```javascript
// Page: US Letter (612 x 792 pt)
// Image: 1020 x 1320 px (150 DPI)

const screen = scaleBboxToScreen(
  { left: 72, bottom: 650, right: 540, top: 720 },
  612, 792,  // PDF dimensions
  1020, 1320 // Image dimensions
);

console.log(screen);
// {
//   x: 120.00,
//   y: 120.00,
//   width: 780.00,
//   height: 116.67
// }
```

### Rendered SVG

```html
<svg viewBox="0 0 1020 1320">
  <rect
    x="120"
    y="120"       <!-- Low Y = near top ✅ -->
    width="780"
    height="116.67"
    fill="#4b5563"
    fill-opacity="0.15"
    stroke="#4b5563"
    stroke-width="2"
  />
</svg>
```

---

## Common Mistakes

### Mistake 1: Using PDF Y directly

```javascript
// ❌ WRONG
screenY = pdfBbox.top * scaleY  // 720 * 1.667 = 1200

// This puts the heading near the BOTTOM of the image!
// But the heading is at the TOP of the PDF!
```

### Mistake 2: Flipping bottom instead of top

```javascript
// ❌ WRONG
screenTop = pdfBbox.top * scaleY  // No flip
screenBottom = imageHeight - (pdfBbox.bottom * scaleY)  // Flip

// This produces negative heights!
```

### Mistake 3: Confusing PDF variable names

```javascript
// ⚠️ CAREFUL - Variable names can be misleading!
// In some PDFs, 't' might mean 'top' or might mean the first Y coordinate
// Always verify which coordinate is higher!

// In Docling:
pdfBbox.top > pdfBbox.bottom  // Always true (top is higher Y)
```

---

## Testing Y-Flip

### Quick Test

```javascript
// Test 1: Element at PDF top should be at screen top
const pdfTop = { left: 72, bottom: 650, right: 540, top: 720 };
const screenTop = scaleBboxToScreen(pdfTop, 612, 792, 1020, 1320);

console.assert(screenTop.y < 300, 'Top element should be near screen top');
// ✅ screenTop.y = 120 (near top)

// Test 2: Element at PDF bottom should be at screen bottom
const pdfBottom = { left: 150, bottom: 100, right: 462, top: 300 };
const screenBottom = scaleBboxToScreen(pdfBottom, 612, 792, 1020, 1320);

console.assert(screenBottom.y > 700, 'Bottom element should be near screen bottom');
// ✅ screenBottom.y = 820 (near bottom)
```

### Visual Test

1. Open `test-bbox-overlay.html`
2. Run Test 3: Coordinate System Validation
3. Check that:
   - Heading (PDF top=720) → Screen y=120 (near top) ✅
   - Picture (PDF top=300) → Screen y=820 (near bottom) ✅

---

## Summary

| Concept | PDF | Screen | Transformation |
|---------|-----|--------|----------------|
| **Origin** | Bottom-left | Top-left | Coordinate flip |
| **Y direction** | Upward ↑ | Downward ↓ | Subtract from height |
| **Top of page** | High Y (e.g., 720) | Low Y (e.g., 120) | `imageHeight - pdfY` |
| **Bottom of page** | Low Y (e.g., 100) | High Y (e.g., 820) | `imageHeight - pdfY` |

**Golden Rule:** `screenY = imageHeight - (pdfY * scaleY)`

This ensures elements appear in the correct position on screen, matching their position in the PDF.

---

## References

- **PDF Coordinate System:** Adobe PDF Reference Manual, Section 4.2
- **PostScript:** PostScript Language Reference Manual, Chapter 4
- **SVG Coordinate System:** W3C SVG 2.0 Specification, Section 7.1
- **Implementation:** `src/frontend/utils/coordinate-scaler.js`
- **Validation:** `tests/frontend/validate-coordinate-scaling.js`

---

**Key Takeaway:** Always flip Y-coordinates when converting from PDF (bottom-left origin) to screen/SVG (top-left origin). The formula `screenY = imageHeight - (pdfY * scaleY)` is critical for correct positioning.
