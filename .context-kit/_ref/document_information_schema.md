# Document Information Schema

**Version**: 1.0
**Last Updated**: 2025-10-13
**Status**: Production

## Overview

This document defines the complete information schema for documents in the tkr-docusearch system. It catalogs all metadata, content, and structural information available for each processed document.

## Purpose

- **Design Reference**: For building document information pages and viewers
- **API Contract**: Defines what data can be retrieved via `/documents/{doc_id}` endpoint
- **Storage Schema**: Documents ChromaDB metadata structure
- **Integration Guide**: For UI components that display document details

---

## Core Document Metadata

Available for **all documents**, regardless of format.

### Identity & Location

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `doc_id` | string(64) | SHA-256 hash identifier (unique) | Generated from file content |
| `filename` | string(255) | Original filename | Upload/webhook |
| `source_path` | string | Path to original uploaded file | File system |
| `date_added` | ISO 8601 | Timestamp when processed (UTC) | Processing pipeline |

### Counts & Collections

| Field | Type | Description |
|-------|------|-------------|
| `page_count` | integer | Total number of pages/screens |
| `chunk_count` | integer | Number of text chunks created |
| `collections` | string[] | Collections containing document: `["visual"]`, `["text"]`, or `["visual", "text"]` |
| `has_images` | boolean | Whether page images are available |

### Storage Information

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 | When stored in ChromaDB (UTC) |
| `embedding_shape` | string | Dimensions like `"(1031, 128)"` |
| `seq_length` | integer | Number of tokens in embedding |

---

## Visual/Page Information

Available for **PDFs, images, PowerPoint, and other visual formats**.

Each page in `pages[]` array contains:

### Page Identity

| Field | Type | Description |
|-------|------|-------------|
| `page_number` | integer | 1-indexed page number |
| `embedding_id` | string | ChromaDB ID (format: `{doc_id}-page{page:03d}`) |

### Page Images

| Field | Type | Description | Resolution |
|-------|------|-------------|------------|
| `image_path` | string | URL to full-resolution page image | 150 DPI PNG |
| `thumb_path` | string | URL to thumbnail image | ~200px wide JPG |

URL format: `/images/{doc_id}/page{page:03d}.png` or `/images/{doc_id}/page{page:03d}_thumb.jpg`

### Page Embeddings

| Field | Type | Description |
|-------|------|-------------|
| `full_embeddings` | compressed base64 | Multi-vector embedding (gzip compressed) |
| `seq_length` | integer | Token count (typical: 1031 for images) |
| `embedding_shape` | string | Shape like `"(1031, 128)"` |

---

## Text/Chunk Information

Available for **documents with extracted text** (all formats).

Each chunk in `chunks[]` array contains:

### Chunk Identity

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | string | Chunk identifier (format: `chunk_{n}`) |
| `embedding_id` | string | ChromaDB ID (format: `{doc_id}-chunk{n:04d}`) |
| `page` | integer | Source page number |

### Chunk Content

| Field | Type | Description |
|-------|------|-------------|
| `text_content` | string | Full text content of chunk |
| `text_preview` | string | First 200 characters (for lists/previews) |
| `word_count` | integer | Number of words in chunk |

**Default chunking**: 250 words per chunk with 50-word overlap.

### Chunk Embeddings

| Field | Type | Description |
|-------|------|-------------|
| `full_embeddings` | compressed base64 | Multi-vector embedding (gzip compressed) |
| `seq_length` | integer | Token count (typical: ~30 for text chunks) |
| `embedding_shape` | string | Shape like `"(30, 128)"` |

---

## Processing Status Metadata

Tracks document lifecycle through the processing pipeline.

### Status Tracking

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `status` | enum | `queued`, `parsing`, `embedding_visual`, `embedding_text`, `storing`, `completed`, `failed` | Current processing status |
| `progress` | float | 0.0 - 1.0 | Progress value |
| `stage` | string | - | Human-readable current stage |

### Progress Details

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer? | Current page being processed (null if not applicable) |
| `total_pages` | integer? | Total pages in document (null if not applicable) |

### Timing Information

| Field | Type | Description |
|-------|------|-------------|
| `started_at` | ISO 8601 | Processing start time (UTC) |
| `updated_at` | ISO 8601 | Last update time (UTC) |
| `completed_at` | ISO 8601? | Completion time (UTC), null if not completed |
| `elapsed_time` | float | Seconds elapsed since processing started |
| `estimated_remaining` | float? | Estimated seconds remaining (null if unavailable) |

### Error Tracking

| Field | Type | Description |
|-------|------|-------------|
| `error` | string? | Error message if status is `failed`, null otherwise |

---

## Enhanced Document Structure

Available when **Enhanced Mode** is enabled (Docling structure extraction).

Provides rich semantic metadata extracted during parsing.

### Document Structure Object

Stored in `metadata.structure` (compressed):

```typescript
{
  headings: HeadingInfo[],
  tables: TableInfo[],
  pictures: PictureInfo[],
  code_blocks: CodeBlockInfo[],
  formulas: FormulaInfo[],
  summary: {
    total_sections: number,
    max_heading_depth: number,
    has_table_of_contents: boolean
  }
}
```

### Summary Statistics

| Field | Type | Description |
|-------|------|-------------|
| `num_headings` | integer | Total heading count |
| `num_tables` | integer | Total table count |
| `num_pictures` | integer | Total picture/figure count |
| `max_heading_depth` | integer | Maximum heading nesting level |
| `total_sections` | integer | Total section count |
| `has_table_of_contents` | boolean | Whether document has TOC |

### Heading Information

Each heading in `headings[]`:

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Heading text content |
| `level` | enum | `TITLE`, `SECTION_HEADER`, `SUB_SECTION_HEADER`, `PARAGRAPH_HEADER` |
| `page` | integer | Page number where heading appears |
| `section_path` | string | Breadcrumb trail (e.g., "Introduction > Methods > Data") |
| `bbox` | float[4]? | Bounding box `[x1, y1, x2, y2]` if available |

### Table Information

Each table in `tables[]`:

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number |
| `caption` | string? | Table caption if available |
| `rows` | integer | Number of rows |
| `cols` | integer | Number of columns |
| `has_header` | boolean | Whether table has header row |
| `table_id` | string | Unique identifier (e.g., "table-0") |
| `bbox` | float[4]? | Bounding box coordinates |

### Picture Information

Each picture in `pictures[]`:

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number |
| `type` | enum | `chart`, `diagram`, `photo`, `logo`, `signature`, `other` |
| `caption` | string? | Picture caption if available |
| `confidence` | float | Classification confidence (0-1) |
| `picture_id` | string | Unique identifier (e.g., "picture-0") |
| `bbox` | float[4]? | Bounding box coordinates |

### Code Block Information

Each code block in `code_blocks[]` (if enabled):

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number |
| `language` | string? | Detected programming language |
| `lines` | integer | Number of lines |
| `bbox` | float[4]? | Bounding box coordinates |

### Formula Information

Each formula in `formulas[]` (if enabled):

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number |
| `latex` | string? | LaTeX representation |
| `bbox` | float[4]? | Bounding box coordinates |

---

## Text Chunk Context

Available when **Enhanced Mode** is enabled.

Provides contextual information for each text chunk in `chunk_context`:

| Field | Type | Description |
|-------|------|-------------|
| `parent_heading` | string? | Immediate parent heading text |
| `parent_heading_level` | integer? | Parent heading level (0=title, 1=section, etc.) |
| `section_path` | string | Breadcrumb trail (e.g., "Intro > Methods > Data") |
| `element_type` | enum | `text`, `list_item`, `table_cell`, `caption`, `code`, `formula` |
| `related_tables` | string[] | IDs of tables mentioned in chunk |
| `related_pictures` | string[] | IDs of pictures mentioned in chunk |
| `page_nums` | integer[] | Pages spanned by chunk (usually 1) |
| `is_page_boundary` | boolean | Whether chunk crosses page boundary |

---

## Audio File Metadata

Available when **audio files** (MP3/WAV) are processed.

### ID3 Tags

Stored with `audio_` prefix in ChromaDB metadata:

| Field | Type | Description |
|-------|------|-------------|
| `audio_title` | string? | Track title |
| `audio_artist` | string? | Artist name |
| `audio_album` | string? | Album name |
| `audio_album_artist` | string? | Album artist |
| `audio_year` | string? | Release year |
| `audio_genre` | string? | Genre |
| `audio_track_number` | string? | Track number |
| `audio_composer` | string? | Composer name |
| `audio_comment` | string? | Comment (truncated to 1000 chars) |
| `audio_publisher` | string? | Publisher/label |

### Audio Properties

| Field | Type | Description |
|-------|------|-------------|
| `audio_duration_seconds` | float | Duration in seconds |
| `audio_bitrate_kbps` | integer | Bitrate in kbps |
| `audio_sample_rate_hz` | integer | Sample rate in Hz |
| `audio_channels` | integer | Number of channels (1=mono, 2=stereo) |
| `audio_encoder` | string? | Encoder used |

### Album Art

| Field | Type | Description |
|-------|------|-------------|
| `has_album_art` | boolean | Whether album art exists |
| `album_art_path` | string? | URL to saved album art image (format: `/images/{doc_id}/cover.jpg`) |
| `album_art_mime` | string? | MIME type (`image/jpeg`, `image/png`) |
| `album_art_size_bytes` | integer? | File size in bytes |
| `album_art_description` | string? | Optional description |

Album art is saved to: `data/images/{doc_id}/cover.{jpg|png}`

---

## Full Document Content

### Markdown Extraction

| Field | Type | Description |
|-------|------|-------------|
| `full_markdown` | string | Complete markdown extraction of document |
| `full_markdown_compressed` | base64 | Gzip-compressed markdown (if >1KB) |
| `markdown_compression` | enum | `none`, `gzip+base64` |
| `markdown_extracted` | boolean | Whether extraction succeeded |

**Retrieval**: Use `ChromaClient.get_document_markdown(doc_id)` to retrieve and decompress.

**Compression**: Applied automatically if markdown exceeds 1KB threshold.

---

## Search Result Metadata

When documents appear in search results, additional fields are included:

### Ranking Information

| Field | Type | Description |
|-------|------|-------------|
| `score` | float | Final relevance score (0-1) |
| `stage1_score` | float | Initial HNSW retrieval score |
| `stage2_score` | float | Late interaction MaxSim re-ranking score |
| `rank` | integer | Position in search results (1-indexed) |

### Search Context

| Field | Type | Description |
|-------|------|-------------|
| `search_mode` | enum | `visual_only`, `text_only`, or `hybrid` |
| `matched_collection` | string | Which collection matched: `visual` or `text` |
| `query` | string | Original search query |

---

## Storage & Technical Metadata

### Embedding Information

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `visual` or `text` |
| `embedding_shape` | string | Dimensions (e.g., `"(1031, 128)"`) |
| `seq_length` | integer | Token count |
| `compression_ratio` | float | ~4x with gzip compression |

**Embedding Model**: ColNomic 7B (nomic-ai/colnomic-embed-multimodal-7b)
**Embedding Dimension**: 128 (CLS token for retrieval)
**Acceleration**: Metal Performance Shaders (MPS) on M1/M2/M3 Macs

### ChromaDB Collections

| Collection | Purpose | ID Format |
|------------|---------|-----------|
| `visual_collection` | Page-level visual embeddings | `{doc_id}-page{page:03d}` |
| `text_collection` | Chunk-level text embeddings | `{doc_id}-chunk{chunk_id:04d}` |

### Storage Estimates

| Item | Size |
|------|------|
| Visual embedding (compressed) | ~50KB per page |
| Text embedding (compressed) | ~5KB per chunk |
| Full markdown (compressed) | ~10-50KB per document |
| Page image (full) | ~100-500KB per page (PNG) |
| Page thumbnail | ~10-30KB per page (JPG) |
| Album art | ~50-200KB per document |

---

## API Response Format

### GET /documents/{doc_id}

Complete response structure:

```typescript
{
  doc_id: string,              // SHA-256 hash
  filename: string,            // Original filename
  date_added: string,          // ISO 8601 timestamp

  pages: [                     // Array of page info
    {
      page_number: number,
      image_path: string,      // URL to full image
      thumb_path: string,      // URL to thumbnail
      embedding_id: string
    }
  ],

  chunks: [                    // Array of text chunks
    {
      chunk_id: string,
      text_content: string,
      embedding_id: string
    }
  ],

  metadata: {
    page_count: number,
    chunk_count: number,
    has_images: boolean,
    collections: string[],
    raw_metadata: {            // All ChromaDB metadata
      ...                      // Includes all fields above
    }
  }
}
```

### GET /documents

List response includes subset:

```typescript
{
  documents: [
    {
      doc_id: string,
      filename: string,
      page_count: number,
      chunk_count: number,
      date_added: string,
      collections: string[],
      has_images: boolean,
      first_page_thumb: string  // URL to first page thumbnail
    }
  ],
  total: number,
  limit: number,
  offset: number
}
```

---

## Format-Specific Behavior

### PDF Documents
- ✅ Visual embeddings (page images)
- ✅ Text embeddings (extracted text)
- ✅ Enhanced structure (headings, tables, figures)
- ✅ Full markdown extraction
- ✅ Page images (full + thumbnails)

### Image Files (JPEG, PNG)
- ✅ Visual embeddings (single page)
- ❌ Text embeddings (no text)
- ❌ Enhanced structure
- ❌ Markdown extraction
- ✅ Page image (full + thumbnail)

### PowerPoint (PPTX)
- ✅ Visual embeddings (slides)
- ✅ Text embeddings (slide text)
- ✅ Limited structure (slide order)
- ✅ Markdown extraction
- ✅ Slide images (full + thumbnails)

### Word Documents (DOCX)
- ❌ Visual embeddings (text-only format)
- ✅ Text embeddings
- ✅ Enhanced structure (headings, tables)
- ✅ Full markdown extraction
- ❌ Page images

### Audio Files (MP3, WAV)
- ❌ Visual embeddings (text-only)
- ✅ Text embeddings (transcription)
- ❌ Enhanced structure
- ✅ Transcript as markdown
- ✅ Album art (if present)
- ✅ ID3 tags and audio properties

### Text Files (TXT, MD, CSV)
- ❌ Visual embeddings (text-only)
- ✅ Text embeddings
- ❌ Enhanced structure
- ✅ Full markdown extraction
- ❌ Page images

---

## Data Retrieval Methods

### ChromaDB Client Methods

```python
# Get full document markdown
markdown = client.get_document_markdown(doc_id)

# Get visual embeddings for document
visual_data = client._visual_collection.get(where={"doc_id": doc_id})

# Get text embeddings for document
text_data = client._text_collection.get(where={"doc_id": doc_id})

# Get full embeddings for re-ranking
embeddings = client.get_full_embeddings(embedding_id, collection="visual")

# Get collection statistics
stats = client.get_collection_stats()
```

### API Endpoints

```bash
# List all documents
GET /documents?limit=50&offset=0&search=report&sort_by=date_added

# Get document details
GET /documents/{doc_id}

# Get page image
GET /images/{doc_id}/page001.png

# Get thumbnail
GET /images/{doc_id}/page001_thumb.jpg

# Get album art
GET /images/{doc_id}/cover.jpg

# Get processing status
GET /status/{doc_id}

# Get processing queue
GET /status/queue
```

---

## Security & Validation

### Document ID Validation

- **Pattern**: `^[a-zA-Z0-9\-]{8,64}$`
- **Type**: SHA-256 hash (64 hex characters)
- **Purpose**: Prevent path traversal attacks

### Filename Validation (Images)

- **Pattern**: `^(page\d{3}(_thumb\.jpg|\.png)|cover\.(jpg|jpeg|png))$`
- **Valid Examples**: `page001.png`, `page001_thumb.jpg`, `cover.jpg`
- **Purpose**: Prevent directory traversal

### Metadata Size Limits

- **Max metadata size**: 50KB per embedding
- **Max structure size**: 200KB per document
- **Comment truncation**: 1000 characters for audio comments
- **Text preview**: 200 characters for chunk previews

---

## Performance Characteristics

### Processing Times

| Operation | Time |
|-----------|------|
| Image embedding | ~2.3s per page (Metal GPU) |
| Text embedding | ~0.24s per chunk (Metal GPU) |
| Full document parsing | ~5-30s depending on size |
| Search (hybrid) | ~239ms average |

### Storage Efficiency

| Metric | Value |
|--------|-------|
| Embedding compression | ~4x (gzip) |
| Markdown compression | ~3-5x (gzip, if >1KB) |
| Metadata overhead | <50KB per embedding |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-13 | Initial comprehensive schema documentation |

---

## See Also

- **AUDIO_METADATA_SCHEMA.md**: Detailed audio metadata specification
- **docling_implementation.md**: Document parsing implementation details
- **Integration contracts**: `/integration-contracts/03-documents-api.contract.md`
- **Storage schema**: `/src/storage/metadata_schema.py`
- **API models**: `/src/processing/documents_api.py`
