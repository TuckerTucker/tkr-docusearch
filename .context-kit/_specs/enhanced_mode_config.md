# Enhanced Mode Configuration

**Version**: 1.0
**Last Updated**: 2025-10-13
**Status**: Enabled

## Overview

Enhanced mode is now **ENABLED** by default in the document processor. It provides rich document structure extraction, semantic chunking, and metadata enrichment using Docling's advanced features.

## What You Get With Enhanced Mode

### Document Structure Extraction
- **Headings**: Hierarchical heading detection with section paths
- **Tables**: Table structure recognition with row/column counts and captions
- **Pictures**: Image classification (chart, diagram, photo, logo, etc.)
- **Code Blocks**: Programming language detection (optional)
- **Formulas**: LaTeX extraction (optional)

### Smart Chunking
- **Hybrid Strategy**: Document-aware chunking that respects structure
- **Context Preservation**: Each chunk knows its parent heading and section
- **Peer Merging**: Adjacent small chunks with same headings are merged

### Enhanced Metadata
- Rich metadata stored in ChromaDB for filtering and search
- Bounding box coordinates for all elements
- Section paths like "Introduction > Methods > Data"
- Element type classification (text, list_item, table_cell, etc.)

---

## Default Configuration

Enhanced mode uses **sensible defaults** that work well for most documents:

| Feature | Default | Description |
|---------|---------|-------------|
| **Table Structure** | ✅ Enabled | TableFormer model for table recognition |
| **Picture Classification** | ✅ Enabled | Image type detection (chart/diagram/photo) |
| **Code Enrichment** | ❌ Disabled | Language detection (adds overhead) |
| **Formula Enrichment** | ❌ Disabled | LaTeX extraction (adds overhead) |
| **Chunking Strategy** | Hybrid | Document-aware vs. legacy word-based |
| **Max Chunk Tokens** | 512 | Maximum tokens per chunk |
| **Min Chunk Tokens** | 100 | Minimum tokens per chunk |
| **Merge Peer Chunks** | ✅ Enabled | Merge adjacent chunks with same heading |
| **Table Mode** | Accurate | "accurate" or "fast" |
| **Images Scale** | 2.0 | Image generation scale factor |

---

## Environment Variables

You can customize enhanced mode behavior via environment variables:

### Feature Flags

```bash
# Enable/disable table structure recognition (default: true)
ENABLE_TABLE_STRUCTURE=true

# Enable/disable picture classification (default: true)
ENABLE_PICTURE_CLASSIFICATION=true

# Enable/disable code block language detection (default: false)
# Note: Adds processing overhead
ENABLE_CODE_ENRICHMENT=false

# Enable/disable formula LaTeX extraction (default: false)
# Note: Adds processing overhead
ENABLE_FORMULA_ENRICHMENT=false
```

### Chunking Configuration

```bash
# Chunking strategy: "hybrid" or "legacy" (default: hybrid)
# hybrid = document-aware, respects structure
# legacy = word-based sliding window (backward compatible)
CHUNKING_STRATEGY=hybrid

# Maximum tokens per chunk (default: 512)
# Range: 100-4096
MAX_CHUNK_TOKENS=512

# Minimum tokens per chunk (default: 100)
# Range: 10-1000
MIN_CHUNK_TOKENS=100

# Merge adjacent chunks with same parent heading (default: true)
MERGE_PEER_CHUNKS=true
```

### Pipeline Options

```bash
# TableFormer mode: "fast" or "accurate" (default: accurate)
# fast = faster processing, slightly lower accuracy
# accurate = slower, higher table recognition quality
TABLE_STRUCTURE_MODE=accurate

# Image generation scale factor (default: 2.0)
# Range: 0.5-4.0
# Higher = better quality, larger files
IMAGES_SCALE=2.0
```

---

## Example Configurations

### Maximum Quality (Slower)
```bash
# .env or environment
ENABLE_TABLE_STRUCTURE=true
ENABLE_PICTURE_CLASSIFICATION=true
ENABLE_CODE_ENRICHMENT=true
ENABLE_FORMULA_ENRICHMENT=true
CHUNKING_STRATEGY=hybrid
TABLE_STRUCTURE_MODE=accurate
IMAGES_SCALE=3.0
MAX_CHUNK_TOKENS=512
```

### Balanced (Recommended - Default)
```bash
# .env or environment
ENABLE_TABLE_STRUCTURE=true
ENABLE_PICTURE_CLASSIFICATION=true
ENABLE_CODE_ENRICHMENT=false
ENABLE_FORMULA_ENRICHMENT=false
CHUNKING_STRATEGY=hybrid
TABLE_STRUCTURE_MODE=accurate
IMAGES_SCALE=2.0
MAX_CHUNK_TOKENS=512
```

### Fast Processing (Minimal Overhead)
```bash
# .env or environment
ENABLE_TABLE_STRUCTURE=false
ENABLE_PICTURE_CLASSIFICATION=false
ENABLE_CODE_ENRICHMENT=false
ENABLE_FORMULA_ENRICHMENT=false
CHUNKING_STRATEGY=legacy
TABLE_STRUCTURE_MODE=fast
IMAGES_SCALE=1.0
MAX_CHUNK_TOKENS=256
```

### Legacy Mode (Disable Enhanced Features)
```bash
# To revert to legacy mode, don't pass enhanced_mode_config
# Or use minimal features
ENABLE_TABLE_STRUCTURE=false
ENABLE_PICTURE_CLASSIFICATION=false
CHUNKING_STRATEGY=legacy
```

---

## Performance Impact

### Processing Time Impact

| Feature | Overhead | Notes |
|---------|----------|-------|
| Table Structure (accurate) | +15-30% | TableFormer model inference |
| Table Structure (fast) | +5-10% | Faster but less accurate |
| Picture Classification | +5-10% | Image classification model |
| Code Enrichment | +10-20% | Language detection for code blocks |
| Formula Enrichment | +10-20% | LaTeX extraction |
| Hybrid Chunking | Minimal | Negligible impact |

**Recommendation**: Use default settings (table structure + picture classification, no code/formula enrichment).

### Storage Impact

Enhanced mode adds metadata to ChromaDB:

| Metadata Type | Size per Document |
|---------------|-------------------|
| Document Structure | ~10-100KB (compressed) |
| Chunk Context | ~1-5KB per chunk |
| Total Overhead | ~5-10% increase |

---

## Testing Enhanced Mode

### Restart Worker

After changing environment variables, restart the worker:

```bash
# Stop current worker
./scripts/stop-all.sh

# Start with new config
./scripts/start-all.sh

# Check logs
tail -f logs/worker-native.log
```

### Verify Configuration

Check startup logs for confirmation:

```
✓ Enhanced mode enabled: table_structure=True, picture_classification=True, chunking=hybrid
✓ Document processor initialized (enhanced mode)
```

### Test Document Processing

Upload a test document and check the metadata:

```python
from src.storage import ChromaClient

client = ChromaClient(host="localhost", port=8001)

# Get document metadata
visual_data = client._visual_collection.get(
    where={"filename": "test.pdf"},
    limit=1,
    include=["metadatas"]
)

metadata = visual_data['metadatas'][0]

# Check for enhanced metadata
print("Has structure:", metadata.get("has_structure", False))
print("Num headings:", metadata.get("num_headings", 0))
print("Num tables:", metadata.get("num_tables", 0))
print("Num pictures:", metadata.get("num_pictures", 0))
```

---

## Document Types & Structure Extraction

### PDF Documents
- ✅ Full structure extraction (headings, tables, pictures)
- ✅ Hybrid chunking with context
- ✅ Bounding boxes for all elements

### Word Documents (DOCX)
- ✅ Headings and tables
- ✅ Hybrid chunking with context
- ⚠️ No pictures (text-only processing)

### PowerPoint (PPTX)
- ⚠️ Limited structure (slide order only)
- ✅ Text chunks with slide context
- ✅ Visual embeddings for each slide

### Markdown/HTML/Text
- ⚠️ Limited structure (heading detection only)
- ✅ Text chunks with basic context
- ❌ No visual processing

### Audio Files (MP3/WAV)
- ❌ No structure extraction
- ✅ Transcript chunks with timestamps
- ✅ Audio metadata (separate system)

---

## Troubleshooting

### Enhanced Mode Not Working

**Check logs for errors:**
```bash
tail -f logs/worker-native.log | grep -i "enhanced"
```

**Verify configuration loaded:**
```bash
# Should see in logs:
# "Loading enhanced mode configuration..."
# "✓ Enhanced mode enabled: ..."
```

**Check environment variables:**
```bash
# Print current environment
env | grep -E "(ENABLE_|CHUNKING_|TABLE_|MAX_CHUNK)"
```

### No Structure Metadata

**Possible causes:**
1. Document type doesn't support structure (e.g., plain text)
2. ENABLE_TABLE_STRUCTURE=false
3. Document has no detectable structure
4. Processing failed during structure extraction (check logs)

**Check specific document:**
```python
# Get metadata and check has_structure flag
metadata = client._visual_collection.get(
    where={"doc_id": "your-doc-id"},
    limit=1,
    include=["metadatas"]
)['metadatas'][0]

print("has_structure:", metadata.get("has_structure", False))
```

### Performance Issues

**If processing is too slow:**

1. Disable expensive features:
   ```bash
   ENABLE_CODE_ENRICHMENT=false
   ENABLE_FORMULA_ENRICHMENT=false
   TABLE_STRUCTURE_MODE=fast
   ```

2. Reduce image scale:
   ```bash
   IMAGES_SCALE=1.0
   ```

3. Use legacy chunking:
   ```bash
   CHUNKING_STRATEGY=legacy
   ```

---

## Migration Notes

### From Legacy Mode

**Existing documents** processed in legacy mode:
- ❌ Will NOT have structure metadata
- ✅ Can still be searched normally
- ℹ️ Re-process to get enhanced metadata

**New documents** after enabling enhanced mode:
- ✅ Will have full structure metadata
- ✅ Will have chunk context
- ✅ Better search relevance

### Re-processing Documents

To add enhanced metadata to existing documents:

1. Delete old embeddings:
   ```bash
   # Via copyparty webhook or API
   POST /delete
   {
     "file_path": "/uploads/document.pdf",
     "filename": "document.pdf"
   }
   ```

2. Re-upload document:
   - Will be processed with enhanced mode
   - Gets full structure metadata

---

## API Changes

Enhanced mode **does not change** the API interface:
- ✅ Same endpoints (`/documents`, `/documents/{doc_id}`)
- ✅ Same response format
- ✅ Additional metadata fields populated
- ✅ Backward compatible

New optional fields in metadata:
- `has_structure`: boolean
- `num_headings`, `num_tables`, `num_pictures`: integers
- `structure`: compressed structure data
- `chunk_context`: semantic context for chunks

---

## See Also

- **document_information_schema.md**: Complete metadata schema
- **docling_implementation.md**: Docling parsing details
- **src/config/processing_config.py**: Source code for configuration
- **src/processing/structure_extractor.py**: Structure extraction implementation
- **src/processing/smart_chunker.py**: Hybrid chunking implementation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-13 | Enhanced mode enabled by default, configuration guide created |
