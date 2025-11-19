# Multi-Format Document Support

DocuSearch supports **23 document formats** with intelligent processing strategies optimized for each format type, including automatic conversion of legacy Office formats.

## Supported Formats

### Visual Formats (Full Processing)
**Processing**: Visual embeddings + Text embeddings
**Use case**: Documents with meaningful visual layout (charts, diagrams, formatted content)

| Format | Extension | Description |
|--------|-----------|-------------|
| PDF | `.pdf` | Portable Document Format with full layout analysis |
| PNG | `.png` | Portable Network Graphics |
| JPEG | `.jpg`, `.jpeg` | JPEG images |
| TIFF | `.tiff` | Tagged Image File Format |
| BMP | `.bmp` | Bitmap images |
| WEBP | `.webp` | Modern web image format |

### Text-Only Formats (Optimized Processing)
**Processing**: Text embeddings only (skips visual embedding)
**Use case**: Documents where visual layout is not semantically important

| Format | Extension | Description |
|--------|-----------|-------------|
| **Office Documents** |
| Microsoft Word | `.docx` | Word documents |
| **Legacy Office** (Auto-Converted) |
| Word 97-2003 | `.doc` | Legacy Word documents (auto-converted to .docx) |
| Word Template | `.dot` | Legacy Word templates (auto-converted to .docx) |
| **Modern Office** |
| Microsoft Excel | `.xlsx` | Excel spreadsheets |
| Microsoft PowerPoint | `.pptx` | PowerPoint presentations |
| **Web & Markup** |
| Markdown | `.md` | Markdown formatted text |
| HTML | `.html`, `.htm` | Web pages |
| XHTML | `.xhtml` | XHTML documents |
| AsciiDoc | `.asciidoc` | Technical documentation markup |
| **Data** |
| CSV | `.csv` | Comma-separated values |
| **Specialized** |
| USPTO XML | `.xml` | Patent documents |
| JATS XML | `.xml` | Scientific articles |
| Docling JSON | `.json` | Native Docling format |

### Audio Formats (Transcript Processing)
**Processing**: Text embeddings from transcript only
**Use case**: Audio files with speech content

| Format | Extension | Description |
|--------|-----------|-------------|
| WebVTT | `.vtt` | Web Video Text Tracks (subtitles/captions) |
| WAV | `.wav` | Waveform audio (with ASR) |
| MP3 | `.mp3` | MPEG audio (with ASR) |

## Processing Strategies

### Visual Processing (PDF, Images)
```
Document → Docling Parser → Pages with Images → Visual Embeddings + Text Embeddings → ChromaDB
                                                 ├─ visual_collection (page images)
                                                 └─ text_collection (text chunks)
```

**Characteristics:**
- Full ColPali visual embeddings (1031 tokens × 128 dim per page)
- Text chunk embeddings (30 tokens × 128 dim per chunk)
- Both stored in ChromaDB for hybrid search
- Processing time: ~2.3s per page (Metal GPU)

### Text-Only Processing (MD, HTML, DOCX, CSV, etc.)
```
Document → Docling Parser → Pages with NO Images → Text Embeddings Only → ChromaDB
                                                     └─ text_collection (text chunks)
```

**Characteristics:**
- Skips visual embedding generation (page.image = None)
- Only text chunk embeddings stored
- **10-20x faster** processing (no image encoding)
- **50% storage savings** (no visual embeddings)
- Text search still highly effective

### Legacy Office Processing (.doc, .dot)
```
.doc File → Auto-Detection → Conversion Service → .docx File → Text-Only Processing
                             (LibreOffice)
```

**Characteristics:**
- Automatic conversion to modern .docx format (1-5s typical)
- Original filename preserved in metadata
- Processed as text-only format after conversion
- User sees original `.doc` filename in UI
- See [Legacy Office Conversion Guide](LEGACY_OFFICE_CONVERSION.md) for details

### Audio Processing (VTT, WAV, MP3)
```
Audio File → Docling Parser (ASR/VTT) → Transcript → Text Embeddings → ChromaDB
                                                      └─ text_collection
```

**Characteristics:**
- Extracts transcript via ASR or parses VTT
- Text-only search on transcript content
- No visual embeddings

## Configuration

### Enable/Disable Formats

All formats configured in `docker/.env`:

```bash
SUPPORTED_FORMATS=pdf,doc,dot,docx,pptx,xlsx,md,html,htm,xhtml,asciidoc,csv,png,jpg,jpeg,tiff,bmp,webp,vtt,wav,mp3,xml,json
```

**Note:** `.doc` and `.dot` files are automatically converted to `.docx` before processing.

To add/remove formats, edit this line and restart services:

```bash
./scripts/stop-all.sh
./scripts/start-all.sh
```

### Per-Format Behavior

Format detection is automatic based on file extension. The system determines:

1. **Format Type**: `get_format_type(file_path)` → `VISUAL`, `TEXT_ONLY`, or `AUDIO`
2. **Processing Strategy**: Automatically skips visual embeddings for text-only/audio
3. **Storage**: Only creates ChromaDB entries for generated embeddings

## Performance Comparison

### Visual Formats (PDF, Images)
- **Processing**: 2.3s per page (with Metal GPU)
- **Search latency**: ~239ms (visual + text search)
- **Storage**: ~50KB per page (compressed visual embeddings)

### Text-Only Formats (MD, HTML, DOCX)
- **Processing**: **~0.24s per chunk** (10x faster)
- **Search latency**: **~100ms** (text-only search)
- **Storage**: **~5KB per chunk** (50% savings)

## Search Behavior

### Mixed Format Collections

When your collection contains both visual and text-only documents:

- **Visual formats**: Searchable by visual similarity + text content
- **Text-only formats**: Searchable by text content only
- **Search engine**: Automatically handles mixed results

Example:
```python
# Search across all documents
results = search_engine.search(
    query="What are the key features?",
    top_k=10
)

# Results may include:
# - PDFs (ranked by visual + text similarity)
# - Markdown files (ranked by text similarity)
# - Images (ranked by visual similarity)
```

## Metadata

All processed documents include format metadata:

```python
{
    "format": "md",                    # File extension
    "format_type": "text",             # visual, text, or audio
    "has_images": False,               # Whether visual embeddings exist
    "num_pages": 1,
    # ... other metadata
}
```

## Limitations

| Format | Limitation | Workaround |
|--------|-----------|-----------|
| Audio (WAV, MP3) | Requires ASR model | Use VTT (pre-transcribed) or ensure Docling ASR available |
| Images | OCR quality depends on image clarity | Use high-resolution source images |
| Excel (XLSX) | Complex formulas may not render | Text extraction only |
| HTML | External CSS/images not loaded | Content-only extraction |
| Legacy .doc | Password-protected files not supported | Decrypt file before upload |
| Legacy .doc | VBA macros stripped during conversion | Macros not needed for search |
| Legacy .doc | Digital signatures removed | Signatures not needed for search |

## Examples

### Upload PDF (Visual Processing)
```bash
curl -F "file=@report.pdf" http://localhost:8000/upload
# → Full visual + text processing
# → ~2.3s per page
# → Visual + text embeddings stored
```

### Upload Markdown (Text-Only)
```bash
curl -F "file=@readme.md" http://localhost:8000/upload
# → Text-only processing
# → ~0.24s per chunk
# → Only text embeddings stored
```

### Upload Legacy .doc (Auto-Converted)
```bash
curl -F "file=@quarterly_report.doc" http://localhost:8000/upload
# → Auto-detected as legacy format
# → Converted to .docx (~2s typical)
# → Text-only processing
# → Original filename preserved ("quarterly_report.doc")
```

### Upload Image (Visual Processing)
```bash
curl -F "file=@chart.png" http://localhost:8000/upload
# → Treated as single-page visual document
# → Full visual embedding
# → OCR text extraction
```

## Testing

Run format detection tests:

```bash
python3 src/processing/test_multiformat.py
```

Expected output:
```
✓ Format Detection PASSED (16/16 formats)
✓ Format Categories PASSED (21 total formats)
✓ Configuration Loading PASSED
```

## Troubleshooting

### Format Not Supported
```
Error: Unsupported format: xyz
```
→ Add `.xyz` to `SUPPORTED_FORMATS` in `docker/.env` and restart

### Text-Only Format Shows "No Visual Embeddings"
→ This is expected behavior! Text-only formats intentionally skip visual processing for speed

### Audio Transcription Fails
→ Check Docling ASR availability or use VTT (pre-transcribed) format instead

## Architecture

Format detection logic: `src/processing/docling_parser.py`

```python
from src.processing.docling_parser import get_format_type, FormatType

format_type = get_format_type("document.md")
# → FormatType.TEXT_ONLY

format_type = get_format_type("chart.png")
# → FormatType.VISUAL
```

Processing coordinator: `src/processing/processor.py`

```python
# Automatically skips visual processing for text-only
has_visual_content = any(page.image is not None for page in pages)

if has_visual_content:
    visual_results = visual_processor.process_pages(pages)
else:
    # Skip visual embeddings for text-only formats
    visual_results = []
```
