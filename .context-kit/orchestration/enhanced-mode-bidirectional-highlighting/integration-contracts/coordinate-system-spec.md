# Coordinate System Specification

**Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: FINAL FOR IMPLEMENTATION

---

## Overview

This document defines the coordinate system used for bounding box (bbox) positioning in the DocuSearch enhanced mode bidirectional highlighting feature. All bbox coordinates returned from backend APIs use this standardized system.

## Coordinate System Definition

### Origin and Axes

```
(0,0) ──────────────────────────────────────> X (horizontal)
  │
  │
  │
  │
  │
  │
  v

  Y (vertical)
```

**Origin**: Top-left corner of the page image (0, 0)
**X-axis**: Increases from left to right
**Y-axis**: Increases from top to bottom

This is the standard web/canvas coordinate system used by HTML5 Canvas, SVG, and CSS positioning.

---

## Bounding Box Format

### Array Structure

All bounding boxes are represented as a 4-element array:

```json
[x1, y1, x2, y2]
```

Where:
- `x1`: X-coordinate of the **top-left** corner
- `y1`: Y-coordinate of the **top-left** corner
- `x2`: X-coordinate of the **bottom-right** corner
- `y2`: Y-coordinate of the **bottom-right** corner

### Visual Representation

```
                    ┌─────────────────────────────────┐
                    │                                 │
                    │                                 │
                    │                                 │
                    │       (x1, y1)                  │
                    │           ┌────────────────┐    │
                    │           │                │    │
                    │           │   BOUNDING     │    │
                    │           │   BOX AREA     │    │
                    │           │                │    │
                    │           └────────────────┘    │
                    │                   (x2, y2)      │
                    │                                 │
                    │                                 │
                    │                                 │
                    └─────────────────────────────────┘

         Page Image (width × height)
```

### Dimensions Calculation

```javascript
const width = x2 - x1;
const height = y2 - y1;
const area = width * height;
```

---

## Units and Scale

### Absolute Pixel Coordinates

**Units**: Pixels
**Reference**: Original page image dimensions as rendered by the document processor

All coordinates are in **absolute pixels** relative to the **original full-resolution page image**.

### Example

For a standard US Letter page rendered at 72 DPI:
- Image width: 612 pixels
- Image height: 792 pixels
- Valid X range: [0, 612]
- Valid Y range: [0, 792]

A heading bbox might be:
```json
[50.5, 100.0, 545.8, 125.3]
```

Interpretation:
- Top-left: (50.5px, 100.0px) - roughly 0.7 inches from left, 1.4 inches from top
- Bottom-right: (545.8px, 125.3px)
- Width: 495.3px (about 6.9 inches)
- Height: 25.3px (about 0.35 inches - typical heading height)

---

## Responsive Scaling for Frontend Display

### The Challenge

Page images are displayed at different sizes based on:
- User's viewport size
- Responsive design breakpoints
- Zoom level
- Container constraints

The original image might be 612×792 pixels, but displayed at 400×519 pixels.

### Scaling Formula

The frontend **MUST** scale bbox coordinates to match the displayed image size:

```javascript
// Get original image dimensions (from API response)
const originalWidth = coordinateSystem.image_width;   // e.g., 612
const originalHeight = coordinateSystem.image_height; // e.g., 792

// Get displayed image dimensions (from DOM)
const displayedWidth = imageElement.offsetWidth;   // e.g., 400
const displayedHeight = imageElement.offsetHeight; // e.g., 519

// Calculate scale factors
const scaleX = displayedWidth / originalWidth;     // 400 / 612 = 0.653
const scaleY = displayedHeight / originalHeight;   // 519 / 792 = 0.655

// Scale bbox coordinates
const [x1, y1, x2, y2] = originalBbox;

const displayedBbox = {
  x1: x1 * scaleX,
  y1: y1 * scaleY,
  x2: x2 * scaleX,
  y2: y2 * scaleY
};
```

### Implementation Example

```javascript
/**
 * Scale bounding box coordinates for display
 *
 * @param {Array<number>} bbox - Original bbox [x1, y1, x2, y2]
 * @param {number} originalWidth - Original image width in pixels
 * @param {number} originalHeight - Original image height in pixels
 * @param {number} displayedWidth - Displayed image width in pixels
 * @param {number} displayedHeight - Displayed image height in pixels
 * @returns {Object} Scaled bbox with {x1, y1, x2, y2, width, height}
 */
function scaleBboxForDisplay(bbox, originalWidth, originalHeight, displayedWidth, displayedHeight) {
  if (!bbox || bbox.length !== 4) {
    return null;
  }

  const [x1, y1, x2, y2] = bbox;
  const scaleX = displayedWidth / originalWidth;
  const scaleY = displayedHeight / originalHeight;

  const scaled = {
    x1: x1 * scaleX,
    y1: y1 * scaleY,
    x2: x2 * scaleX,
    y2: y2 * scaleY
  };

  // Add convenience properties
  scaled.width = scaled.x2 - scaled.x1;
  scaled.height = scaled.y2 - scaled.y1;

  return scaled;
}
```

### CSS Positioning

After scaling, use absolute positioning to overlay bbox highlights:

```css
.bbox-overlay {
  position: absolute;
  border: 2px solid var(--citation-inline);
  background: var(--citation-hover);
  opacity: 0.3;
  pointer-events: none;
  box-sizing: border-box;
}
```

```javascript
// Apply to DOM element
function applyBboxStyle(element, scaledBbox) {
  element.style.left = `${scaledBbox.x1}px`;
  element.style.top = `${scaledBbox.y1}px`;
  element.style.width = `${scaledBbox.width}px`;
  element.style.height = `${scaledBbox.height}px`;
}
```

---

## Validation Rules

### Backend Validation

The backend MUST ensure all bboxes satisfy:

1. **Non-negative coordinates**: `x1 >= 0`, `y1 >= 0`, `x2 >= 0`, `y2 >= 0`
2. **Proper ordering**: `x1 < x2` and `y1 < y2`
3. **Within image bounds**:
   - `x2 <= image_width`
   - `y2 <= image_height`
4. **Minimum size**: `(x2 - x1) >= 1` and `(y2 - y1) >= 1` (at least 1 pixel)

### Frontend Validation

The frontend SHOULD validate received bboxes:

```javascript
function validateBbox(bbox, imageWidth, imageHeight) {
  if (!bbox || !Array.isArray(bbox) || bbox.length !== 4) {
    return false;
  }

  const [x1, y1, x2, y2] = bbox;

  // Check all values are numbers
  if (!bbox.every(v => typeof v === 'number' && !isNaN(v))) {
    return false;
  }

  // Validation rules
  return (
    x1 >= 0 && y1 >= 0 &&
    x1 < x2 && y1 < y2 &&
    x2 <= imageWidth && y2 <= imageHeight
  );
}
```

---

## Edge Cases and Handling

### 1. Missing Bounding Box (`bbox: null`)

**When it occurs**:
- Element structure extracted but bbox not available from Docling
- Audio transcripts (no visual representation)
- Legacy documents

**Handling**:
```javascript
if (bbox === null || bbox === undefined) {
  // No visual highlighting possible
  // Fall back to text-only highlight in markdown
  highlightMarkdownChunk(chunkId);
  return;
}
```

### 2. Very Small Bounding Boxes

Minimum visual size for user interaction:

```javascript
const MIN_DISPLAY_SIZE = 10; // pixels

function ensureMinimumSize(scaledBbox) {
  const { x1, y1, width, height } = scaledBbox;

  return {
    x1,
    y1,
    x2: x1 + Math.max(width, MIN_DISPLAY_SIZE),
    y2: y1 + Math.max(height, MIN_DISPLAY_SIZE),
  };
}
```

### 3. Bounding Boxes Spanning Multiple Pages

**Rule**: Each bbox is **always** constrained to a single page.

If an element spans pages (e.g., table continued on next page), the backend provides:
- Separate bbox for each page
- Same element ID referenced on multiple pages
- Frontend handles separately

### 4. Responsive Image Container Changes

Listen for resize events and recalculate:

```javascript
const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    if (entry.target === imageElement) {
      // Recalculate all bbox overlays
      updateAllBboxOverlays();
    }
  }
});

resizeObserver.observe(imageElement);
```

---

## API Response Contract

The `coordinate_system` field in structure responses provides reference dimensions:

```json
{
  "coordinate_system": {
    "origin": "top-left",
    "units": "pixels",
    "image_width": 612,
    "image_height": 792
  }
}
```

**Frontend requirement**: Use these values as `originalWidth` and `originalHeight` for scaling calculations.

---

## Complete Example Workflow

### 1. Backend Returns Structure

```json
{
  "doc_id": "abc123",
  "page": 5,
  "headings": [
    {
      "text": "Methods",
      "bbox": [50.5, 200.0, 545.8, 230.0]
    }
  ],
  "coordinate_system": {
    "image_width": 612,
    "image_height": 792
  }
}
```

### 2. Frontend Receives and Scales

```javascript
// Original dimensions from API
const originalWidth = 612;
const originalHeight = 792;
const originalBbox = [50.5, 200.0, 545.8, 230.0];

// Current displayed size (example)
const displayedWidth = 450;
const displayedHeight = 583;

// Scale
const scaleX = 450 / 612; // = 0.735
const scaleY = 583 / 792; // = 0.736

const displayedBbox = [
  50.5 * 0.735,  // = 37.1
  200.0 * 0.736, // = 147.2
  545.8 * 0.735, // = 401.2
  230.0 * 0.736  // = 169.3
];
```

### 3. Render Overlay

```javascript
const overlay = document.createElement('div');
overlay.className = 'bbox-overlay';
overlay.style.left = '37.1px';
overlay.style.top = '147.2px';
overlay.style.width = '364.1px';  // 401.2 - 37.1
overlay.style.height = '22.1px';  // 169.3 - 147.2

imageContainer.appendChild(overlay);
```

---

## Testing Checklist

Frontend agents implementing bbox rendering should verify:

- [ ] Bboxes scale correctly when window resizes
- [ ] Bboxes align with visual elements in page image
- [ ] Minimum size enforced for tiny elements
- [ ] Null bboxes handled gracefully (no errors)
- [ ] Multiple bboxes on same page don't overlap incorrectly
- [ ] Bboxes scroll into view when chunk highlighted
- [ ] Different page sizes (Letter, A4, Legal) handled correctly
- [ ] High DPI displays render bboxes crisply
- [ ] Zoom in/out maintains bbox alignment
- [ ] Mobile responsive breakpoints scale correctly

---

## Diagram: Complete Coordinate System

```
Original Image: 612×792 pixels               Displayed Image: 400×519 pixels
┌─────────────────────────────┐             ┌──────────────────────┐
│ (0,0)                       │             │ (0,0)                │
│                             │             │                      │
│   Backend bbox:             │    Scale    │   Frontend bbox:     │
│   [50, 100, 546, 125]       │   ────→     │   [33, 66, 357, 82]  │
│                             │   0.653×    │                      │
│   ┌────────────────┐        │   0.655×    │   ┌──────────┐       │
│   │  Heading       │        │             │   │ Heading  │       │
│   └────────────────┘        │             │   └──────────┘       │
│                             │             │                      │
│                             │             │                      │
│                             │             │                      │
│                             │             │                      │
│                             │             │                      │
│                   (612,792) │             │           (400,519)  │
└─────────────────────────────┘             └──────────────────────┘
```

---

## References

- **API Contracts**: `./api-contracts.md` - Full endpoint specifications
- **Sample Responses**: `./sample-api-responses.json` - Realistic bbox examples
- **Frontend Implementation**: Agent 8 (BoundingBox Overlay) will use this spec
- **Backend Implementation**: Agent 4 (Structure API) must produce compliant coordinates

---

## Version History

**v1.0** (2025-10-17):
- Initial coordinate system specification
- Origin: top-left (0,0)
- Units: pixels
- Scaling formulas defined
- Validation rules established
- Edge case handling documented
