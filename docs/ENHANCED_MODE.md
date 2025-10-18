# Enhanced Mode User Guide

**Version:** 1.0
**Last Updated:** 2025-10-17
**Status:** Production Ready

---

## Overview

Enhanced Mode is an advanced feature in DocuSearch that adds **document structure extraction** with **bounding box coordinates** to enable **bidirectional highlighting** between text and visual page representations.

### What is Enhanced Mode?

Enhanced Mode processes documents to extract:
- **Document structure** (headings, paragraphs, lists, tables, figures)
- **Bounding box coordinates** for each structural element
- **Chunk-to-structure mappings** linking text chunks to their visual locations
- **Page-level structure data** for interactive overlays

This enables powerful features like:
- Click a region on a page image → jump to corresponding text
- Hover over text → highlight the region on the page image
- Navigate from research citations directly to specific sections

### Key Benefits

✨ **Bidirectional Navigation** - Seamlessly move between visual and text representations
📍 **Precise Citations** - Research answers link to exact document locations
🎯 **Structure Visualization** - See document structure overlaid on page images
⚡ **Faster Document Exploration** - Jump directly to relevant sections
🔍 **Enhanced Search** - Combine visual and semantic search with structural context

---

## Features in Detail

### 1. Visual Structure Overlay

When viewing document details, page images display colored regions showing:
- **Headings** - Blue outlines
- **Paragraphs** - Green outlines
- **Lists** - Orange outlines
- **Tables** - Purple outlines
- **Figures** - Red outlines

**How to Use:**
1. Open any document details page
2. Scroll to page images
3. See colored regions on each page
4. Click any region to jump to corresponding text

### 2. Bidirectional Highlighting

**Text → Visual:**
- Hover over any text chunk in markdown view
- Corresponding region highlights on page image
- Page scrolls into view if needed

**Visual → Text:**
- Click any colored region on page image
- Corresponding text chunk highlights
- Markdown scrolls to show the text

### 3. Research Integration

Research bot citations now include **chunk indicators** (📍):

```
According to the quarterly report [1]📍, revenue increased 15% year-over-year.
```

**How to Use:**
1. Ask a research question
2. Look for citations with 📍 icon
3. Click "Details" on the reference card
4. Automatically jump to the cited chunk on the document page

### 4. Keyboard Navigation

| Key | Action |
|-----|--------|
| **Tab** | Navigate between regions and chunks |
| **Enter** | Activate focused region/chunk |
| **Space** | Toggle chunk highlight |
| **Escape** | Clear all highlights |
| **Arrow Keys** | Move between regions on page |

---

## Enabling Enhanced Mode

### Prerequisites

- Python 3.10+
- Existing DocuSearch installation
- 2GB+ additional disk space (for structure cache)

### Step 1: Enable via Environment Variable

Edit your environment file:

```bash
# Add to .env or export
export ENHANCED_MODE=true
```

Or edit `docker/.env`:

```bash
ENHANCED_MODE=true
```

### Step 2: Restart Services

```bash
# Stop all services
./scripts/stop-all.sh

# Start with enhanced mode
./scripts/start-all.sh

# Verify enhanced mode is active
./scripts/status.sh
```

You should see:
```
✓ Enhanced Mode: Enabled
```

### Step 3: Process Documents

**Option A: Process New Documents**
- Upload new documents via Copyparty
- They automatically process with enhanced mode

**Option B: Reprocess Existing Documents**

```bash
# Reprocess all documents
python scripts/migrate_enhanced_mode.py --reprocess-all

# Or reprocess specific document
python scripts/migrate_enhanced_mode.py --doc-id "document_id"
```

**Option C: Lazy Migration**
- Flag existing documents for reprocessing
- They reprocess when first accessed

```bash
python scripts/migrate_enhanced_mode.py --lazy
```

---

## Configuration

### Environment Variables

```bash
# Core Settings
ENHANCED_MODE=true              # Enable/disable enhanced mode (default: false)
STRUCTURE_CACHE_SIZE=20         # Number of pages to cache in memory (default: 20)
STRUCTURE_COMPRESSION=true      # Compress structure data (default: true)

# Advanced Settings
STRUCTURE_EXTRACTION_TIMEOUT=30 # Max seconds per page (default: 30)
STRUCTURE_MIN_CONFIDENCE=0.7    # Min confidence for structure elements (default: 0.7)
BBOX_COORDINATE_PRECISION=2     # Decimal places for coordinates (default: 2)
```

### Performance Tuning

**For Large Documents (100+ pages):**
```bash
STRUCTURE_CACHE_SIZE=50         # Increase cache
STRUCTURE_COMPRESSION=true      # Keep compression enabled
```

**For Memory-Constrained Systems:**
```bash
STRUCTURE_CACHE_SIZE=10         # Reduce cache
STRUCTURE_COMPRESSION=true      # Essential for memory savings
```

**For Maximum Speed:**
```bash
STRUCTURE_CACHE_SIZE=100        # Large cache
STRUCTURE_COMPRESSION=false     # Faster decompression (uses more memory)
```

---

## Usage Examples

### Example 1: Research to Document Navigation

**Scenario:** You asked "What are the financial projections?" and got an answer with citations.

**Steps:**
1. Look for 📍 icon next to citation numbers: `[1]📍`
2. Click "Details" button on Reference #1
3. Document page opens with:
   - Page automatically scrolled to cited section
   - Cited chunk highlighted in yellow
   - Corresponding bounding box highlighted on page image
4. Read the context around the citation

**Result:** You found the exact location in seconds, not minutes.

### Example 2: Visual Document Exploration

**Scenario:** You want to understand a complex technical document's structure.

**Steps:**
1. Open document details page
2. Scroll through page images
3. Observe colored regions showing:
   - Section headings (blue)
   - Body paragraphs (green)
   - Code blocks (purple)
   - Figures (red)
4. Click interesting region to read corresponding text
5. Hover over text to see its location on page

**Result:** You quickly grasped the document structure without reading everything.

### Example 3: Finding Specific Content

**Scenario:** You remember seeing a table but forgot which page.

**Steps:**
1. Open document details
2. Look for purple (table) regions on page thumbnails
3. Click the table region
4. Corresponding markdown table appears
5. Hover over table text to confirm it's the right one

**Result:** Found the table in seconds instead of scanning all pages.

---

## Understanding the Interface

### Document Details Page (Enhanced)

```
┌─────────────────────────────────────────────────────────┐
│  Document: quarterly_report.pdf                          │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │  Page 1         │  │  Markdown Content            │  │
│  │  [Image with    │  │  # Q4 Financial Report       │  │
│  │   colored       │  │  ## Executive Summary  ◄─────┼──┼─ Hover highlights
│  │   regions]  ────┼──┼► Revenue increased 15%... │  │  │
│  │                 │  │                              │  │
│  │  Click region   │  │  ## Revenue Breakdown        │  │
│  │  jumps to text──┼─►│  - Product A: $50M          │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Research Page with Citations

```
┌────────────────────────────────────────────────────────────┐
│  Question: What were the Q4 results?                       │
├────────────────────────────────────────────────────────────┤
│  Answer:                         │  References:            │
│  ┌────────────────────────────┐  │  ┌──────────────────┐  │
│  │ Revenue increased 15% [1]📍│  │  │ [1] report.pdf   │  │
│  │ in Q4 2024, driven by      │  │  │     Page 3       │  │
│  │ strong product sales [1]📍.│  │  │     [Details] ◄──┼──┼─ Click to jump
│  │                            │  │  └──────────────────┘  │  to chunk
│  │ Profit margins improved    │  │                        │
│  │ to 23% [2], exceeding      │  │  [2] analysis.pdf     │
│  │ guidance [2]📍.             │  │      Page 7           │
│  └────────────────────────────┘  │      [Details]        │
└────────────────────────────────────────────────────────────┘
       Hover citation → Highlight reference
       Hover reference → Highlight citations
```

---

## Troubleshooting

### Enhanced Mode Not Enabled

**Symptom:** No colored regions on page images, no 📍 icons in research citations.

**Cause:** Enhanced mode not enabled or services not restarted.

**Solution:**
```bash
# Check current status
./scripts/status.sh

# If "Enhanced Mode: Disabled"
export ENHANCED_MODE=true
./scripts/stop-all.sh
./scripts/start-all.sh
```

### Existing Documents Not Enhanced

**Symptom:** New documents show enhanced features, old documents don't.

**Cause:** Old documents processed before enhanced mode was enabled.

**Solution:**
```bash
# Option 1: Reprocess all (slow but thorough)
python scripts/migrate_enhanced_mode.py --reprocess-all

# Option 2: Lazy migration (fast, on-demand)
python scripts/migrate_enhanced_mode.py --lazy

# Option 3: Specific document only
python scripts/migrate_enhanced_mode.py --doc-id "doc_12345"
```

### Bounding Boxes Don't Align

**Symptom:** Colored regions don't match text content.

**Cause:** Coordinate transformation error or cached structure data.

**Solution:**
```bash
# Clear structure cache
rm -rf data/structure_cache/*

# Reprocess the document
python scripts/migrate_enhanced_mode.py --doc-id "problematic_doc_id"
```

### Performance Degradation

**Symptom:** Page loads slowly, high memory usage.

**Cause:** Structure cache too large or compression disabled.

**Solution:**
```bash
# Reduce cache size
export STRUCTURE_CACHE_SIZE=10

# Ensure compression enabled
export STRUCTURE_COMPRESSION=true

# Restart services
./scripts/stop-all.sh && ./scripts/start-all.sh
```

### Structure Extraction Failed

**Symptom:** Document processed but no structure data available.

**Cause:** Complex document layout or extraction timeout.

**Solution:**
```bash
# Increase timeout
export STRUCTURE_EXTRACTION_TIMEOUT=60

# Lower confidence threshold
export STRUCTURE_MIN_CONFIDENCE=0.5

# Retry processing
python scripts/migrate_enhanced_mode.py --doc-id "failed_doc_id"
```

### Highlights Don't Clear

**Symptom:** Clicking regions/chunks doesn't clear previous highlights.

**Cause:** JavaScript event listeners not attached.

**Solution:**
1. Refresh the page (Ctrl+R or Cmd+R)
2. Clear browser cache if problem persists
3. Check browser console for JavaScript errors

---

## Performance Considerations

### Processing Time

Enhanced mode adds processing overhead:

| Document Type | Standard Mode | Enhanced Mode | Overhead |
|---------------|---------------|---------------|----------|
| 10-page PDF | ~23s | ~30s | +30% |
| 50-page PDF | ~115s | ~150s | +30% |
| 100-page DOCX | ~24s | ~32s | +33% |

**Why?** Structure extraction analyzes each page to identify elements and calculate bounding boxes.

### Storage Impact

Enhanced mode increases storage requirements:

| Data Type | Size per Page | Compression Ratio |
|-----------|---------------|-------------------|
| Structure JSON | ~5KB | 4:1 (with gzip) |
| Bounding Boxes | ~2KB | 3:1 (with gzip) |
| Chunk Mappings | ~1KB | 2:1 (with gzip) |

**Total:** ~2KB per page with compression enabled (~8KB without)

**Example:** 100-page document = ~200KB additional storage (vs ~800KB uncompressed)

### Memory Usage

Structure cache holds decompressed data in memory:

```
Memory = STRUCTURE_CACHE_SIZE × Avg_Page_Structure_Size
       = 20 pages × 8KB
       = 160KB (negligible)
```

Even with 100 pages cached: ~800KB (still minimal)

### Network Impact

Enhanced mode API responses include chunk IDs:

| Response Type | Standard Mode | Enhanced Mode | Overhead |
|---------------|---------------|---------------|----------|
| Search Results | ~2KB | ~2.5KB | +25% |
| Research Answer | ~10KB | ~12KB | +20% |
| Structure Data | N/A | ~8KB/page | New |

**Mitigation:** Compression reduces overhead to ~5-10% in practice.

---

## Migration Guide

### Migrating from Standard Mode

**Step 1: Assess Current State**

```bash
# Check how many documents exist
python scripts/validate_migration.py --count-documents

# Estimate migration time
python scripts/migrate_enhanced_mode.py --dry-run --reprocess-all
```

**Step 2: Choose Migration Strategy**

**Strategy A: Reprocess All (Recommended for <100 docs)**
- **Pros:** Clean, consistent, all features available immediately
- **Cons:** Takes time, requires downtime
- **Use When:** Small to medium collections, overnight maintenance window

```bash
python scripts/migrate_enhanced_mode.py --reprocess-all
```

**Strategy B: Lazy Migration (Recommended for >100 docs)**
- **Pros:** Fast, no downtime, gradual migration
- **Cons:** Mixed experience until all accessed
- **Use When:** Large collections, can't afford downtime

```bash
python scripts/migrate_enhanced_mode.py --lazy
```

**Strategy C: Flag Legacy (Quickest)**
- **Pros:** Instant, no reprocessing, backward compatible
- **Cons:** Old docs lack enhanced features forever
- **Use When:** Only care about new documents

```bash
python scripts/migrate_enhanced_mode.py --flag-legacy
```

**Step 3: Execute Migration**

```bash
# Full reprocess (example: 50 docs × 30s = 25 minutes)
python scripts/migrate_enhanced_mode.py --reprocess-all

# Monitor progress
tail -f logs/migration.log
```

**Step 4: Validate**

```bash
# Run validation suite
python scripts/validate_migration.py

# Check report
cat migration_validation_report.txt
```

**Step 5: Verify Enhanced Features**

1. Open a migrated document
2. Confirm colored regions appear
3. Test bidirectional highlighting
4. Ask a research question
5. Verify 📍 icons and chunk navigation

---

## FAQ

### Q: Do I need enhanced mode?

**A:** It depends on your use case:

**You NEED it if:**
- You use the research bot frequently
- You want precise citation navigation
- You work with complex structured documents
- Visual navigation is important

**You DON'T need it if:**
- You only do basic keyword search
- Storage is extremely constrained
- Processing time is critical
- You have very simple documents

### Q: Can I disable enhanced mode later?

**A:** Yes, but:

```bash
export ENHANCED_MODE=false
./scripts/stop-all.sh && ./scripts/start-all.sh
```

**What happens:**
- New documents process without structure extraction
- Existing enhanced documents retain their structure data
- Enhanced features still work for documents that have structure data
- No data is lost

### Q: Does it work with all document types?

**A:** Support varies:

| Format | Structure Extraction | Bounding Boxes | Notes |
|--------|---------------------|----------------|-------|
| PDF | ✅ Full | ✅ Accurate | Best support |
| DOCX | ✅ Full | ⚠️ Approximate | Word layout varies |
| PPTX | ✅ Full | ✅ Accurate | Per-slide bboxes |
| MP3/WAV | ❌ N/A | ❌ N/A | Audio has no structure |
| TXT | ⚠️ Limited | ❌ N/A | No visual layout |

### Q: How much does it slow down processing?

**A:** Approximately +30% processing time per document.

**Example:**
- Standard: 10-page PDF = 23 seconds
- Enhanced: 10-page PDF = 30 seconds (+7 seconds)

**Mitigation:** Processing is async, so you won't notice during upload.

### Q: Can I customize region colors?

**A:** Not currently via UI, but you can edit CSS:

```css
/* src/frontend/styles/document-details.css */
.bbox-heading { border-color: blue; }
.bbox-paragraph { border-color: green; }
.bbox-list { border-color: orange; }
.bbox-table { border-color: purple; }
.bbox-figure { border-color: red; }
```

### Q: What if structure extraction fails?

**A:** Document still processes normally:
- Embeddings generated
- Search works
- Markdown available
- Enhanced features gracefully disabled for that document

No data loss, partial degradation only.

### Q: Does it work with scanned PDFs?

**A:** Limited support:
- OCR text is extracted
- Structure detection may be inaccurate
- Bounding boxes approximate
- Best with native PDFs

### Q: Can I export structure data?

**A:** Yes, via API:

```bash
# Get structure for page 1 of document
curl http://localhost:8002/documents/doc_12345/pages/1/structure

# Returns JSON with bboxes and element types
```

---

## Advanced Usage

### Programmatic Access

**Get Structure Data:**

```python
import requests

# Fetch structure for a page
response = requests.get(
    "http://localhost:8002/documents/doc_12345/pages/1/structure"
)
structure = response.json()

# Access bounding boxes
for element in structure["elements"]:
    print(f"{element['type']}: {element['bbox']}")
    # heading: {'left': 72, 'bottom': 650, 'right': 540, 'top': 720}
```

**Get Chunk with Metadata:**

```python
# Fetch specific chunk
response = requests.get(
    "http://localhost:8002/documents/doc_12345/chunks/chunk_5"
)
chunk = response.json()

print(f"Text: {chunk['text']}")
print(f"Page: {chunk['page']}")
print(f"Bbox: {chunk['bbox']}")
```

### Custom Highlighting

**Highlight Specific Elements:**

```javascript
// JavaScript to highlight a specific element type
document.querySelectorAll('.bbox-heading').forEach(el => {
    el.style.borderColor = 'red';
    el.style.borderWidth = '3px';
});
```

### Integration with External Tools

**Export for Annotation:**

```bash
# Export structure as JSON
curl http://localhost:8002/documents/doc_12345/structure > structure.json

# Convert to annotation format (e.g., COCO)
python scripts/convert_structure_to_coco.py structure.json > annotations.json
```

---

## Security Considerations

### Data Privacy

Enhanced mode extracts additional metadata but:
- ✅ All data stays local (no external calls)
- ✅ Structure data stored in ChromaDB (same as embeddings)
- ✅ No additional cloud dependencies
- ✅ Same security model as standard mode

### Access Control

Structure data respects document permissions:
- Users can only access structure for documents they can view
- No elevation of privileges
- API endpoints require same authentication as document endpoints

### Performance Impact

Potential DoS considerations:
- Structure extraction is rate-limited (same as document processing)
- Cache prevents repeated extraction
- Timeout prevents infinite processing

---

## Version History

**v1.0 (2025-10-17)**
- Initial enhanced mode release
- Structure extraction with bounding boxes
- Bidirectional highlighting
- Research integration with chunk navigation
- Migration tools
- Comprehensive documentation

**Planned for v1.1:**
- Streaming structure extraction
- Custom region styling via UI
- Multi-column layout support
- Enhanced OCR integration
- Structure-aware search ranking

---

## Additional Resources

- **[Bidirectional Highlighting Guide](BIDIRECTIONAL_HIGHLIGHTING.md)** - Technical deep-dive
- **[API Reference](API_ENHANCED_ENDPOINTS.md)** - Complete API documentation
- **[Developer Guide](DEVELOPER_GUIDE_BBOX.md)** - Coordinate system and implementation details
- **[Migration Scripts](../scripts/migrate_enhanced_mode.py)** - Source code for migration
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

---

**Questions? Issues?** Open a GitHub issue or contact the development team.

**Enjoy Enhanced Mode! 🚀📍**
