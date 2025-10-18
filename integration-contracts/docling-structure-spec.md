# Docling DocumentStructure Coordinate System Specification

**Version:** 1.0
**Date:** 2025-10-17
**Status:** VALIDATED

## Overview

This document specifies the coordinate system used by Docling for bounding box annotations in DocumentStructure. All backend and frontend agents implementing structure visualization must adhere to this specification.

---

## Bounding Box Format

### Format

Docling returns bounding boxes as tuples of 4 floating-point numbers:

```python
bbox = (left, bottom, right, top)
# Also represented as: (l, b, r, t)
# Or in array notation: [x1, y1, x2, y2]
# NOTE: y1=bottom, y2=top (bottom-left origin)
```

### Components

**⚠️ IMPORTANT: Docling uses BOTTOM-LEFT origin (native PDF coordinate system)**

| Component | Symbol | Description | Constraints |
|-----------|--------|-------------|-------------|
| Left | `l` or `x1` | Left edge of bounding box | `l >= 0` |
| Bottom | `b` or `y1` | **Bottom edge** (lower Y value) | `b >= 0` |
| Right | `r` or `x2` | Right edge of bounding box | `r > l` |
| Top | `t` or `y2` | **Top edge** (higher Y value) | `t > b` |

### Example

```python
# Example from structure_extractor.py
prov_bbox = prov.bbox
bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
# NOTE: Despite the variable name 't' (top), this is actually bottom in PDF coords
# Result: (100.5, 50.2, 250.3, 120.8)
#         (left, bottom, right, top)
```

**CRITICAL:** The extraction code uses `.t` and `.b` attributes, but these represent the **native PDF coordinate system** where:
- `.t` = y-coordinate (may be top OR bottom depending on origin)
- `.b` = y-coordinate (may be bottom OR top depending on origin)

Real-world validation shows `.t` < `.b`, confirming **bottom-left origin**.

---

## Coordinate System

### Origin Point

**⚠️ BOTTOM-LEFT Corner** - The coordinate system origin (0, 0) is at the **bottom-left corner** of the page.

This is the **native PDF/PostScript coordinate system**.

```
Y-axis (bottom to top)
↑
│
│
│
│
(0,0) ────────────────> X-axis (left to right)
```

### Axis Directions

- **X-axis (horizontal):** Increases from **left to right**
- **Y-axis (vertical):** Increases from **BOTTOM to TOP** ⚠️

This is **OPPOSITE** to typical screen/image coordinates!

### Units

**Points (pt)** - PDF coordinate system units (1 point = 1/72 inch)

- **NOT pixels** - Independent of display resolution
- **NOT normalized** - Actual page coordinates, not 0-1 range
- Standard PDF/PostScript point system

### Common Page Sizes (for reference)

| Page Size | Width (pt) | Height (pt) |
|-----------|------------|-------------|
| US Letter | 612 | 792 |
| A4 | 595.3 | 841.9 |
| Legal | 612 | 1008 |

---

## Coordinate Space

### Page Image Dimensions

Bounding boxes are defined in the **page coordinate space**, which corresponds to:

1. **PDF Pages:** Native PDF coordinates (points)
2. **Rendered Images:** Scale factor applied during rendering

### Relationship to Rendered Images

**⚠️ CRITICAL: Coordinate System Conversion Required**

When Docling renders a page to an image, **coordinate conversion is required** because:
- **PDF coords:** Bottom-left origin, Y increases upward
- **Image coords:** Top-left origin, Y increases downward

```python
# Given:
# - bbox in PDF coords: (left, bottom, right, top)
# - page_height in points (e.g., 792 for US Letter)
# - render DPI (e.g., 150)

scale_factor = render_dpi / 72.0
page_height_px = page_height * scale_factor

# Convert PDF bbox to image pixel coordinates
pixel_bbox = (
    bbox[0] * scale_factor,                    # left (same)
    page_height_px - (bbox[3] * scale_factor), # top (flip Y)
    bbox[2] * scale_factor,                    # right (same)
    page_height_px - (bbox[1] * scale_factor)  # bottom (flip Y)
)
```

**Example:**
```python
# PDF bbox: (100, 600, 250, 650)  (left, bottom, right, top)
# Page height: 792 points (US Letter)
# Render DPI: 150
scale_factor = 150 / 72 = 2.0833
page_height_px = 792 * 2.0833 = 1650px

# Image coordinates (top-left origin):
# left = 100 * 2.0833 = 208.33px (same)
# top = 1650 - (650 * 2.0833) = 1650 - 1354.17 = 295.83px (flip)
# right = 250 * 2.0833 = 520.83px (same)
# bottom = 1650 - (600 * 2.0833) = 1650 - 1250.00 = 400.00px (flip)
```

---

## Scaling Requirements for Display

### Frontend Display

**⚠️ CRITICAL: Y-Axis Flip Required**

To display bboxes on rendered page images in the browser:

1. **Get page dimensions:**
   ```javascript
   const imageWidth = img.naturalWidth;   // pixels
   const imageHeight = img.naturalHeight; // pixels
   const pdfWidth = 612;    // points (from metadata)
   const pdfHeight = 792;   // points (from metadata)
   ```

2. **Calculate scale factors:**
   ```javascript
   const scaleX = imageWidth / pdfWidth;
   const scaleY = imageHeight / pdfHeight;
   ```

3. **Convert bbox from PDF to image coordinates:**
   ```javascript
   // Input: bbox = [left, bottom, right, top] (PDF coords)
   const displayBbox = {
     left: bbox[0] * scaleX,
     top: imageHeight - (bbox[3] * scaleY),     // FLIP Y: top
     right: bbox[2] * scaleX,
     bottom: imageHeight - (bbox[1] * scaleY)   // FLIP Y: bottom
   };

   // Calculate width and height
   const width = displayBbox.right - displayBbox.left;
   const height = displayBbox.bottom - displayBbox.top;
   ```

### CSS Positioning

For absolute positioning overlays (with Y-axis flip):

```javascript
// Convert bbox to CSS properties
function bboxToCSS(bbox, pdfWidth, pdfHeight, imageWidth, imageHeight) {
  const scaleX = imageWidth / pdfWidth;
  const scaleY = imageHeight / pdfHeight;

  const left = bbox[0] * scaleX;
  const top = imageHeight - (bbox[3] * scaleY);  // FLIP Y
  const width = (bbox[2] - bbox[0]) * scaleX;
  const height = (bbox[3] - bbox[1]) * scaleY;   // Height same (diff of Y coords)

  return { left, top, width, height };
}
```

```css
.bbox-overlay {
  position: absolute;
  left: /* calculated left */px;
  top: /* calculated top (flipped) */px;
  width: /* calculated width */px;
  height: /* calculated height */px;
  border: 2px solid var(--primary-color);
  pointer-events: none;
}
```

---

## Structure Element Coverage

Bounding boxes are available for the following structure elements:

| Element Type | Bbox Available | Notes |
|--------------|----------------|-------|
| **Headings** | ✓ Yes | `HeadingInfo.bbox` |
| **Tables** | ✓ Yes | `TableInfo.bbox` |
| **Pictures** | ✓ Yes | `PictureInfo.bbox` |
| **Code Blocks** | ✓ Yes | `CodeBlockInfo.bbox` |
| **Formulas** | ✓ Yes | `FormulaInfo.bbox` |

### Availability Notes

- **Not all elements have bboxes** - Some elements may have `bbox = None`
- **Check before use:** Always validate `if element.bbox is not None`
- **Provenance dependent:** Bbox extraction depends on Docling's provenance data

---

## ⚠️ Critical Note: Coordinate Ordering Ambiguity

**IMPORTANT DISCOVERY:** The extraction code variable names are MISLEADING!

```python
# From structure_extractor.py:
bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
```

Real-world data shows:
- `prov_bbox.t` (labeled "top") has **HIGHER** Y values
- `prov_bbox.b` (labeled "bottom") has **LOWER** Y values

In bottom-left origin PDFs:
- **Higher Y = top of page**
- **Lower Y = bottom of page**

Therefore, despite variable names, the actual order is:
```python
bbox = (left, higher_y, right, lower_y)
#      = (left, top_pdf, right, bottom_pdf)  # PDF coords perspective
```

**For downstream agents:** Treat bbox[1] as the **larger Y coordinate** and bbox[3] as the **smaller Y coordinate** when working with bottom-left origin.

---

## Validation Rules

### Constraint Validation

All bboxes must satisfy:

```python
def validate_bbox(bbox: tuple) -> bool:
    """Validate bbox format and constraints."""
    if not isinstance(bbox, (tuple, list)):
        return False
    if len(bbox) != 4:
        return False

    l, t, r, b = bbox

    # All coordinates must be numbers
    if not all(isinstance(c, (int, float)) for c in bbox):
        return False

    # Geometric constraints
    if l >= r:  # left < right
        return False
    if t >= b:  # top < bottom
        return False

    # Non-negative (Docling uses 0-based)
    if l < 0 or t < 0:
        return False

    return True
```

### Test Coverage

See `tests/integration/test_docling_structure.py` for comprehensive validation tests:
- Format validation
- Constraint checking
- Coordinate validity
- Sample data generation

---

## Implementation Reference

### Extraction Code

Bboxes are extracted in `src/processing/structure_extractor.py`:

```python
# Example from _extract_headings()
if hasattr(text_item, "prov") and text_item.prov:
    prov = text_item.prov[0]
    if hasattr(prov, "bbox"):
        try:
            prov_bbox = prov.bbox
            bbox = (prov_bbox.l, prov_bbox.t, prov_bbox.r, prov_bbox.b)
        except (AttributeError, TypeError):
            pass
```

### Storage Schema

Stored in `src/storage/metadata_schema.py`:

```python
@dataclass
class HeadingInfo:
    text: str
    level: HeadingLevel
    page_num: int
    bbox: Optional[Tuple[float, float, float, float]] = None
    section_path: str = ""
```

---

## Edge Cases & Limitations

### Edge Cases

1. **Rotated elements:** Bboxes are axis-aligned, not rotated
2. **Multi-page elements:** Each bbox is per-page, not document-wide
3. **Overlapping bboxes:** Possible for layered content
4. **Clipped elements:** May extend beyond page boundaries (rare)

### Limitations

1. **No polygon support:** Only rectangular bboxes
2. **No rotation metadata:** Rotation angle not provided
3. **No Z-order:** Layer/depth information not available
4. **Approximate bounds:** OCR-based elements may have approximate bboxes

---

## Examples

### Real-World Example (from test document)

```json
{
  "headings": [
    {
      "text": "Introduction",
      "level": "SECTION_HEADER",
      "page_num": 1,
      "bbox": [72.0, 100.5, 540.0, 125.3],
      "section_path": "Introduction"
    }
  ],
  "tables": [
    {
      "table_id": "table-0",
      "page_num": 2,
      "bbox": [100.2, 200.7, 500.8, 450.3],
      "num_rows": 5,
      "num_cols": 3,
      "has_header": true
    }
  ]
}
```

See `integration-contracts/sample-structure.json` for complete examples.

---

## Usage Guidelines

### Backend Agents (Wave 2)

1. **Storage:** Store bboxes as-is in metadata (points)
2. **API Response:** Return bboxes in original units
3. **Validation:** Validate constraints on extraction
4. **Documentation:** Include units in API docs

### Frontend Agents (Wave 3)

1. **Fetch page dimensions:** Get PDF page size from metadata
2. **Calculate scale:** Image pixels / PDF points
3. **Transform bboxes:** Apply scale factor for display
4. **Handle missing:** Gracefully handle `bbox = None`
5. **Visual feedback:** Highlight on hover/click

---

## Testing

### Integration Tests

Run comprehensive validation:

```bash
pytest tests/integration/test_docling_structure.py -v
```

Tests validate:
- Bbox format (4-tuple)
- Constraints (x1 < x2, y1 < y2)
- Non-negative coordinates
- Availability across element types

### Sample Data

Generated by test suite:
- **Location:** `integration-contracts/sample-structure.json`
- **Contents:** Real extracted structure with bboxes
- **Usage:** Reference for frontend/backend development

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-17 | Initial specification based on Docling integration |

---

## References

- **Docling Documentation:** https://github.com/DS4SD/docling
- **PDF Coordinate System:** Adobe PDF Reference Manual
- **Implementation:** `src/processing/structure_extractor.py`
- **Tests:** `tests/integration/test_docling_structure.py`
- **Sample Data:** `integration-contracts/sample-structure.json`

---

## Contact

For questions or clarifications regarding this specification:
- **Project:** tkr-docusearch
- **Author:** Tucker (@tuckertucker)
- **Status:** Production-ready (Wave 6 Complete)
