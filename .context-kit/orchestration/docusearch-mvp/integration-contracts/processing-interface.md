# Processing Interface Contract

**Owner**: processing-agent
**Consumers**: ui-agent (via event hooks)
**Providers**: embedding-agent, storage-agent
**Purpose**: Define document processing workflow, event hooks, and status messaging

---

## Document Processing Workflow

### Overview

The processing pipeline handles uploaded documents through multiple stages:

1. **Document Parsing** - Extract pages and text using Docling
2. **Visual Processing** - Render pages to images, generate embeddings
3. **Text Processing** - Chunk text, generate embeddings
4. **Storage** - Persist embeddings to ChromaDB
5. **Status Updates** - Notify UI of progress

---

## Processing Pipeline Stages

### Stage 1: Document Parsing

**Input**: File path to uploaded document
**Output**: Parsed document structure

```python
@dataclass
class ParsedDocument:
    filename: str                    # Original filename
    doc_id: str                      # Unique identifier (UUID)
    num_pages: int                   # Total page count
    pages: List[Page]                # Page objects
    text_chunks: List[TextChunk]     # Text chunk objects
    metadata: Dict[str, Any]         # Document-level metadata

@dataclass
class Page:
    page_num: int                    # 1-indexed page number
    image: PIL.Image.Image           # Rendered page image
    width: int                       # Image width in pixels
    height: int                      # Image height in pixels
    text: str                        # Extracted page text (for reference)

@dataclass
class TextChunk:
    chunk_id: str                    # Unique chunk identifier
    page_num: int                    # Source page number
    text: str                        # Chunk text content
    start_offset: int                # Character offset in page
    end_offset: int                  # Character offset in page
    word_count: int                  # Approximate word count
```

**Processing**:
- Use Docling parser for PDF/DOCX/PPTX
- Render pages at 150 DPI for visual processing
- Chunk text with 250 word average, 50 word overlap
- Extract metadata (author, created date, title if available)

---

### Stage 2: Visual Processing

**Input**: List of Page objects
**Output**: Visual embeddings ready for storage

```python
@dataclass
class VisualEmbeddingResult:
    doc_id: str
    page_num: int
    embedding: np.ndarray            # Multi-vector (seq_length, 768)
    cls_token: np.ndarray            # Representative vector (768,)
    seq_length: int                  # Token count
    processing_time_ms: int          # Latency metric

def process_visual_batch(pages: List[Page]) -> List[VisualEmbeddingResult]:
    """
    Process visual pages through embedding-agent.

    Calls: embedding-agent.embed_images(images)
    Returns: Visual embedding results for each page

    Performance target: 6s per page (FP16), 3s per page (INT8)
    """
```

---

### Stage 3: Text Processing

**Input**: List of TextChunk objects
**Output**: Text embeddings ready for storage

```python
@dataclass
class TextEmbeddingResult:
    doc_id: str
    chunk_id: str
    page_num: int
    embedding: np.ndarray            # Multi-vector (seq_length, 768)
    cls_token: np.ndarray            # Representative vector (768,)
    seq_length: int                  # Token count
    text: str                        # Original chunk text
    processing_time_ms: int          # Latency metric

def process_text_batch(chunks: List[TextChunk]) -> List[TextEmbeddingResult]:
    """
    Process text chunks through embedding-agent.

    Calls: embedding-agent.embed_texts(texts)
    Returns: Text embedding results for each chunk

    Performance target: 2s per chunk (FP16), 1s per chunk (INT8)
    """
```

---

### Stage 4: Storage

**Input**: Visual and text embedding results
**Output**: ChromaDB storage confirmation

```python
def store_embeddings(
    visual_results: List[VisualEmbeddingResult],
    text_results: List[TextEmbeddingResult],
    doc_metadata: Dict[str, Any]
) -> StorageConfirmation:
    """
    Store all embeddings in ChromaDB.

    Calls:
    - storage-agent.add_visual_embeddings(visual_results)
    - storage-agent.add_text_embeddings(text_results)

    Returns: Confirmation with storage IDs
    """

@dataclass
class StorageConfirmation:
    doc_id: str
    visual_ids: List[str]            # ChromaDB IDs for visual embeddings
    text_ids: List[str]              # ChromaDB IDs for text embeddings
    total_size_bytes: int            # Storage overhead
    timestamp: str                   # ISO 8601 storage time
```

---

## Event Hook Integration

### Copyparty Event Hook

**File**: `data/copyparty/hooks/on_upload.py`

**Trigger**: Called by copyparty when file is uploaded

```python
#!/usr/bin/env python3
"""
Copyparty event hook: Trigger document processing on upload.

Called by copyparty with environment variables:
- CPP_PATH: Full path to uploaded file
- CPP_FN: Filename
- CPP_SIZE: File size in bytes
- CPP_USER: Uploader username (if authenticated)
"""

import os
import subprocess

def on_upload():
    """Trigger processing worker."""
    file_path = os.environ.get('CPP_PATH')
    filename = os.environ.get('CPP_FN')
    file_size = int(os.environ.get('CPP_SIZE', 0))

    # Validate file type
    if not filename.lower().endswith(('.pdf', '.docx', '.pptx')):
        print(f"Skipping unsupported file: {filename}")
        return

    # Check file size (max 100MB)
    max_size_mb = 100
    if file_size > max_size_mb * 1024 * 1024:
        print(f"File too large: {file_size / 1024 / 1024:.1f}MB > {max_size_mb}MB")
        return

    # Trigger processing worker
    subprocess.run([
        'docker', 'compose', 'exec', '-T', 'processing-worker',
        'python', '-m', 'src.processing.worker', 'process', file_path
    ])

if __name__ == '__main__':
    on_upload()
```

---

## Processing Status Messages

### Status Updates

The processing worker emits status messages to allow UI monitoring:

```python
@dataclass
class ProcessingStatus:
    doc_id: str
    filename: str
    status: Literal["queued", "parsing", "embedding_visual",
                    "embedding_text", "storing", "completed", "failed"]
    progress: float                  # 0.0 to 1.0
    stage: str                       # Human-readable stage description
    current_page: Optional[int]      # Current page being processed
    total_pages: Optional[int]       # Total pages in document
    elapsed_seconds: int             # Time since start
    estimated_remaining_seconds: Optional[int]  # ETA
    error_message: Optional[str]     # Error details if failed
    timestamp: str                   # ISO 8601 timestamp

# Status file location
STATUS_FILE = f"/tmp/docusearch/status/{doc_id}.json"
```

**Status Flow**:
1. `queued` - Document added to processing queue
2. `parsing` - Docling parsing in progress (5-10s)
3. `embedding_visual` - Visual processing (6s/page FP16)
4. `embedding_text` - Text processing (2s/chunk FP16)
5. `storing` - Saving to ChromaDB (1-2s)
6. `completed` - Processing successful
7. `failed` - Error occurred (see error_message)

---

## Processing Queue (Wave 4)

### Queue Management

```python
@dataclass
class QueueItem:
    doc_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    priority: int                    # 1 (high) to 5 (low)
    added_timestamp: str             # ISO 8601
    estimated_processing_time_seconds: int

class ProcessingQueue:
    """
    FIFO queue for document processing (Wave 4 enhancement).

    Backend: Redis or file-based queue
    """

    def add(self, file_path: str, priority: int = 3) -> str:
        """Add document to queue, return doc_id."""

    def get_next(self) -> Optional[QueueItem]:
        """Get next item from queue (FIFO with priority)."""

    def get_status(self) -> QueueStatus:
        """Get queue statistics."""

    def remove(self, doc_id: str):
        """Remove item from queue."""

@dataclass
class QueueStatus:
    queue_size: int                  # Items waiting
    processing: int                  # Currently processing (0 or 1)
    completed_today: int             # Completed count (24h)
    failed_today: int                # Failed count (24h)
    avg_processing_time_seconds: float  # Rolling average
    estimated_wait_time_seconds: int    # For next item
```

---

## Error Handling

### Error Categories

```python
class ProcessingError(Exception):
    """Base exception for processing errors."""

class ParsingError(ProcessingError):
    """Document parsing failed (corrupted file, unsupported format)."""

class EmbeddingError(ProcessingError):
    """Embedding generation failed (model error, out of memory)."""

class StorageError(ProcessingError):
    """Storage failed (ChromaDB unavailable, disk full)."""
```

### Error Recovery

**Parsing Errors**:
- Log error with file path
- Update status to `failed` with error message
- Continue processing next document in queue
- Do NOT crash worker

**Embedding Errors**:
- Retry once with smaller batch size
- If still failing, mark as failed and continue
- Log error for debugging

**Storage Errors**:
- Retry up to 3 times with exponential backoff
- If ChromaDB is down, pause queue and alert
- Preserve embeddings in temporary storage for retry

---

## Performance Targets

### Processing Speed

| Document Type | Pages/Chunks | Target Time (FP16) | Target Time (INT8) |
|--------------|--------------|-------------------|-------------------|
| 10-page PDF | 10 pages, 30 chunks | <2 minutes | <1 minute |
| 50-page PDF | 50 pages, 150 chunks | <10 minutes | <5 minutes |
| 100-doc batch | 1000 pages total | <2 hours | <1 hour |

### Resource Usage

- **Memory**: <8GB peak (with INT8 quantization)
- **Disk**: Temporary storage <2x input file size
- **CPU**: 50-80% during processing (MPS offload)

---

## Integration Points

### Calls to embedding-agent

```python
# Visual embeddings
result = embedding_agent.embed_images(
    images=[page.image for page in pages],
    batch_size=4  # Memory-dependent
)

# Text embeddings
result = embedding_agent.embed_texts(
    texts=[chunk.text for chunk in chunks],
    batch_size=8  # Memory-dependent
)
```

### Calls to storage-agent

```python
# Store visual embeddings
storage_agent.add_visual_embeddings(
    embeddings=visual_results,
    metadata=doc_metadata
)

# Store text embeddings
storage_agent.add_text_embeddings(
    embeddings=text_results,
    metadata=doc_metadata
)
```

---

## Testing Requirements

### Unit Tests

- Parse sample PDF, DOCX, PPTX
- Handle corrupted files gracefully
- Validate metadata extraction
- Test text chunking (overlap, word count)

### Integration Tests

- End-to-end: upload → parse → embed → store
- Verify embeddings in ChromaDB after processing
- Test with 10-page PDF (<2 min target)
- Test error recovery (corrupted file, ChromaDB down)

### Mock Requirements (Wave 2)

```python
class MockEmbeddingAgent:
    """Mock for Wave 2 independent development."""

    def embed_images(self, images, batch_size=4):
        # Return dummy multi-vector embeddings
        return {
            "embeddings": [np.random.randn(100, 768) for _ in images],
            "cls_tokens": np.random.randn(len(images), 768)
        }

    def embed_texts(self, texts, batch_size=8):
        # Return dummy multi-vector embeddings
        return {
            "embeddings": [np.random.randn(80, 768) for _ in texts],
            "cls_tokens": np.random.randn(len(texts), 768)
        }

class MockStorageAgent:
    """Mock for Wave 2 independent development."""

    def add_visual_embeddings(self, embeddings, metadata):
        return {"ids": [str(uuid.uuid4()) for _ in embeddings]}

    def add_text_embeddings(self, embeddings, metadata):
        return {"ids": [str(uuid.uuid4()) for _ in embeddings]}
```

---

## Contract Version

**Version**: 1.0
**Last Updated**: 2025-10-06
**Status**: Draft (pending Wave 1 review)

---

## Notes

- Processing worker runs as daemon in processing-worker container
- Event hook triggered synchronously by copyparty (fast return required)
- Queue implementation deferred to Wave 4
- Status updates enable real-time UI monitoring
- Error handling prioritizes worker stability over individual document success
