# Chunk ID Data Flow Diagram

## Overview
This diagram shows how chunk_id flows from ChromaDB storage through the research API to the frontend.

```
┌─────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                             │
│                     (src/storage/)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Store text embedding
                              │ chunk_id: int (0, 1, 2, ...)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CHROMADB                                  │
│                                                                  │
│  Visual Collection              Text Collection                 │
│  ┌─────────────────┐           ┌─────────────────┐             │
│  │ doc123-page001  │           │ doc123-chunk0000│             │
│  │ metadata: {     │           │ metadata: {     │             │
│  │   doc_id,       │           │   doc_id,       │             │
│  │   page: 1,      │           │   chunk_id: 0,  │ ◄───────┐   │
│  │   filename,     │           │   page: 1,      │         │   │
│  │   ...           │           │   filename,     │         │   │
│  │ }               │           │   ...           │         │   │
│  └─────────────────┘           │ }               │         │   │
│                                 └─────────────────┘         │   │
│                                                              │   │
└──────────────────────────────────────────────────────────────┼───┘
                              │                                │
                              │ Search results                 │
                              ▼                                │
┌─────────────────────────────────────────────────────────────────┐
│                     SEARCH ENGINE                                │
│                   (src/search/)                                  │
│                                                                  │
│  Returns results with metadata:                                 │
│  {                                                               │
│    "doc_id": "doc123",                                           │
│    "page": 1,                                                    │
│    "chunk_id": 0,  ◄─────────────────────────────────────────┐  │
│    "score": 0.95,                              Integer from DB│  │
│    ...                                                        │  │
│  }                                                            │  │
└───────────────────────────────────────────────────────────────┼──┘
                              │                                 │
                              │                                 │
                              ▼                                 │
┌─────────────────────────────────────────────────────────────────┐
│                  CONTEXT BUILDER                                 │
│            (src/research/context_builder.py)                     │
│                                                                  │
│  get_source_metadata():                                          │
│  1. Query ChromaDB for page metadata  ────────────────────────┐ │
│  2. Extract chunk_id from metadata                            │ │
│  3. Transform: extract_chunk_id(metadata, doc_id)             │ │
│     ┌────────────────────────────────┐                        │ │
│     │  CHUNK EXTRACTOR               │                        │ │
│     │  (chunk_extractor.py)          │                        │ │
│     │                                 │                        │ │
│     │  Input:  chunk_id: int (0)     │◄───────────────────────┘ │
│     │          doc_id: "doc123"      │                          │
│     │                                 │                          │
│     │  Output: "doc123-chunk0000"    │ ◄─── Format transform   │
│     └────────────────────────────────┘      4-digit zero-pad   │
│                                                                  │
│  4. Create SourceDocument with chunk_id                         │
│     ┌────────────────────────────────┐                          │
│     │  SourceDocument(               │                          │
│     │    doc_id="doc123",            │                          │
│     │    page=1,                     │                          │
│     │    chunk_id="doc123-chunk0000" │ ◄─── String format      │
│     │    ...                         │                          │
│     │  )                             │                          │
│     └────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ ResearchContext with sources
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESEARCH API                                  │
│               (src/api/research.py)                              │
│                                                                  │
│  POST /api/research/ask                                          │
│                                                                  │
│  Build response:                                                 │
│  sources = [                                                     │
│    SourceInfo(                                                   │
│      id=1,                                                       │
│      doc_id=source.doc_id,                                       │
│      chunk_id=source.chunk_id,  ◄───── Pass through from source │
│      ...                                                         │
│    )                                                             │
│  ]                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JSON Response
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HTTP RESPONSE                               │
│                                                                  │
│  {                                                               │
│    "answer": "...",                                              │
│    "citations": [...],                                           │
│    "sources": [                                                  │
│      {                                                           │
│        "id": 1,                                                  │
│        "doc_id": "doc123",                                       │
│        "chunk_id": "doc123-chunk0000",  ◄─── String in response │
│        "page": 1,                                                │
│        ...                                                       │
│      },                                                          │
│      {                                                           │
│        "id": 2,                                                  │
│        "doc_id": "slides456",                                    │
│        "chunk_id": null,  ◄─── null for visual-only results     │
│        "page": 3,                                                │
│        ...                                                       │
│      }                                                           │
│    ]                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│                  (research.html / JS)                            │
│                                                                  │
│  Usage for bidirectional highlighting:                          │
│                                                                  │
│  1. Citation clicked → Find source by id                        │
│  2. Extract chunk_id from source                                │
│  3. Highlight document chunk with matching chunk_id             │
│  4. Document chunk clicked → Find citations referencing chunk   │
│  5. Highlight all matching citations                            │
│                                                                  │
│  Example:                                                        │
│  const source = response.sources[0];                            │
│  if (source.chunk_id) {                                         │
│    highlightChunk(source.chunk_id);                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Data Transformations

### Stage 1: Storage
```
Format: Integer
Example: 0, 1, 2, 45, 9999
Storage: ChromaDB metadata["chunk_id"]
```

### Stage 2: ChromaDB → Search
```
Format: Integer
Example: {"chunk_id": 45}
Transport: Metadata dict from ChromaDB query
```

### Stage 3: Search → Context Builder
```
Input:  metadata["chunk_id"] = 45 (int)
        doc_id = "abc123" (str)

Transform: extract_chunk_id(metadata, doc_id)
          → f"{doc_id}-chunk{chunk_id:04d}"

Output: "abc123-chunk0045" (str)
```

### Stage 4: Context Builder → API
```
Format: String or None
Example: "abc123-chunk0045" or null
Transport: SourceDocument.chunk_id → SourceInfo.chunk_id
```

### Stage 5: API → Frontend
```
Format: String or null (JSON)
Example: {"chunk_id": "abc123-chunk0045"} or {"chunk_id": null}
Transport: JSON response
```

## Visual vs Text Results

### Text Search Result
```
ChromaDB → Search → Context → API → Frontend
chunk_id: 0 → 0 → "doc-chunk0000" → "doc-chunk0000" → "doc-chunk0000"
```

### Visual Search Result
```
ChromaDB → Search → Context → API → Frontend
(no field) → (no field) → None → null → null
```

## Key Functions

1. **extract_chunk_id()** - Main transformation function
   - Input: `metadata: Dict`, `doc_id: str`
   - Output: `Optional[str]` (formatted or None)
   - Location: `src/research/chunk_extractor.py`

2. **parse_chunk_id()** - Reverse parsing (optional utility)
   - Input: `chunk_id_str: str`
   - Output: `Optional[Dict]` (doc_id + chunk_num)
   - Location: `src/research/chunk_extractor.py`

3. **get_source_metadata()** - Integration point
   - Calls: `extract_chunk_id(metadata, doc_id)`
   - Returns: `SourceDocument` with chunk_id field
   - Location: `src/research/context_builder.py`

## Error Handling

```
┌──────────────────────────┐
│ Invalid chunk_id type    │ → Return None (graceful degradation)
│ Missing chunk_id field   │ → Return None (visual result)
│ Parse error              │ → Return None + log warning
│ Negative/invalid number  │ → Format anyway (edge case)
└──────────────────────────┘
```

All errors are handled gracefully without breaking the API response.
