# API Reference

**Version:** 1.0
**Last Updated:** 2025-10-17
**Base URL:** `http://localhost:8002`

---

## Overview

DocuSearch provides RESTful APIs for document processing, search, and research. This reference documents all available endpoints.

---

## Table of Contents

1. [Document Processing](#document-processing)
2. [Search](#search)
3. [Research](#research)
4. [Enhanced Mode Endpoints](#enhanced-mode-endpoints)
5. [Health & Status](#health--status)

---

## Document Processing

### Upload Document

**Endpoint:** `POST /documents/upload`

Upload and process a document.

**Request:**
```bash
curl -X POST "http://localhost:8002/documents/upload" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "doc_id": "doc_abc123",
  "filename": "document.pdf",
  "status": "processing",
  "upload_date": "2025-10-17T12:00:00Z"
}
```

### Get Document

**Endpoint:** `GET /documents/{doc_id}`

Retrieve document metadata.

**Response:**
```json
{
  "doc_id": "doc_abc123",
  "filename": "document.pdf",
  "upload_date": "2025-10-17T12:00:00Z",
  "total_pages": 10,
  "metadata_version": "1.0",
  "has_structure": true
}
```

### Delete Document

**Endpoint:** `DELETE /documents/{doc_id}`

Delete a document and all associated data.

**Response:**
```json
{
  "status": "deleted",
  "visual_deleted": true,
  "text_deleted": true,
  "page_images_deleted": 10,
  "markdown_deleted": true
}
```

---

## Search

### Semantic Search

**Endpoint:** `POST /search`

Perform semantic search across documents.

**Request:**
```json
{
  "query": "quarterly financial results",
  "num_results": 10,
  "mode": "hybrid"
}
```

**Response:**
```json
{
  "query": "quarterly financial results",
  "results": [
    {
      "doc_id": "doc_abc123",
      "filename": "q4_report.pdf",
      "page": 3,
      "score": 0.95,
      "preview": "Revenue increased 15% year-over-year..."
    }
  ],
  "latency_ms": 239
}
```

---

## Research

### Ask Question

**Endpoint:** `POST /api/research/ask`

Submit a research question and receive AI-generated answer with citations.

**Request:**
```json
{
  "question": "What were the Q4 financial results?",
  "num_sources": 10,
  "model": "gpt-4"
}
```

**Response:**
```json
{
  "question": "What were the Q4 financial results?",
  "answer": "Revenue increased 15% [1] to $80M...",
  "sources": [
    {
      "citation_number": 1,
      "doc_id": "doc_abc123",
      "filename": "q4_report.pdf",
      "page": 3,
      "chunk_id": "chunk_abc123_5",
      "bbox": {"left": 72, "bottom": 400, "right": 540, "top": 450},
      "element_type": "paragraph"
    }
  ],
  "processing_time_ms": 2450
}
```

### List Models

**Endpoint:** `GET /api/research/models`

Get available LLM models.

**Response:**
```json
{
  "models": [
    {"id": "gpt-4", "provider": "openai", "name": "GPT-4"},
    {"id": "claude-3-opus", "provider": "anthropic", "name": "Claude 3 Opus"},
    {"id": "gemini-pro", "provider": "google", "name": "Gemini Pro"}
  ]
}
```

---

## Enhanced Mode Endpoints

Enhanced mode provides document structure with bounding boxes for bidirectional highlighting.

### Get Page Structure

**Endpoint:** `GET /documents/{doc_id}/pages/{page}/structure`

Get structure data for a page.

**Request:**
```bash
curl "http://localhost:8002/documents/doc_abc123/pages/1/structure"
```

**Response:**
```json
{
  "doc_id": "doc_abc123",
  "page": 1,
  "page_width": 612,
  "page_height": 792,
  "elements": [
    {
      "id": "elem_1_0",
      "type": "heading",
      "bbox": {"left": 72, "bottom": 650, "right": 540, "top": 720},
      "text": "Executive Summary",
      "chunk_id": "chunk_abc123_0"
    }
  ],
  "has_structure": true
}
```

**See [API_ENHANCED_ENDPOINTS.md](API_ENHANCED_ENDPOINTS.md) for complete enhanced mode API documentation.**

### Get Chunk

**Endpoint:** `GET /documents/{doc_id}/chunks/{chunk_id}`

Get specific chunk with metadata.

**Response:**
```json
{
  "chunk_id": "chunk_abc123_5",
  "doc_id": "doc_abc123",
  "text": "Revenue increased 15% year-over-year...",
  "page": 3,
  "element_id": "elem_3_2",
  "bbox": {"left": 72, "bottom": 400, "right": 540, "top": 450},
  "element_type": "paragraph"
}
```

### Get Markdown with Chunk Markers

**Endpoint:** `GET /documents/{doc_id}/markdown`

Get markdown with HTML comments marking chunk boundaries.

**Response:**
```json
{
  "doc_id": "doc_abc123",
  "filename": "report.pdf",
  "markdown": "<!-- CHUNK_START: chunk_abc123_0, PAGE: 1, BBOX: 72,650,540,720 -->\n# Executive Summary\n<!-- CHUNK_END: chunk_abc123_0 -->",
  "total_chunks": 10,
  "has_structure": true
}
```

---

## Health & Status

### Health Check

**Endpoint:** `GET /health`

Check service health.

**Response:**
```json
{
  "status": "healthy",
  "chromadb": "connected",
  "enhanced_mode": true,
  "version": "1.0.0"
}
```

### Processing Status

**Endpoint:** `GET /status`

Get processing statistics.

**Response:**
```json
{
  "total_documents": 50,
  "processing_queue": 2,
  "last_processed": "2025-10-17T12:00:00Z",
  "avg_processing_time": 30.5
}
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": "Technical details (optional)"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `DOCUMENT_NOT_FOUND` | 404 | Document does not exist |
| `INVALID_REQUEST` | 400 | Malformed request |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| Document upload | 10/min | Per user |
| Search | 100/min | Per user |
| Research ask | 10/min | Per user |
| Enhanced mode | 100/min | Per user |

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
```

---

## Additional Resources

- **[Enhanced Mode Endpoints](API_ENHANCED_ENDPOINTS.md)** - Complete enhanced mode API
- **[Enhanced Mode Guide](ENHANCED_MODE.md)** - User documentation
- **[Developer Guide](DEVELOPER_GUIDE_BBOX.md)** - Coordinate system details
- **[Research Bot Guide](RESEARCH_BOT_GUIDE.md)** - Research features

---

**Questions?** Open an issue at https://github.com/your-org/tkr-docusearch/issues
