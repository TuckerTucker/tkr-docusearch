# Context Builder Interface Contract

**Provider:** Agent 2 - Context Builder
**Consumers:** Agent 4 - Research API
**File:** `src/research/context_builder.py`
**Status:** Wave 1 Foundation Layer
**Version:** 1.0
**Last Updated:** 2025-10-17

---

## Overview

The Context Builder retrieves search results from the existing ColPali/ChromaDB system, extracts document metadata and markdown content, and constructs formatted context strings for LLM consumption with proper citations.

---

## Interface Definition

### Data Classes

```python
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SourceDocument:
    """Represents a source document for citation"""
    doc_id: str  # Unique document identifier
    filename: str  # Original filename (e.g., "report.pdf")
    page: int  # Page number (1-indexed)
    extension: str  # File extension ("pdf", "docx", etc.)

    # Paths for frontend display
    thumbnail_path: Optional[str] = None  # Path to thumbnail image
    image_path: Optional[str] = None  # Full page image

    # Metadata for context
    timestamp: str = ""  # Upload timestamp ISO format
    section_path: Optional[str] = None  # "Introduction > Methods"
    parent_heading: Optional[str] = None  # Immediate parent heading

    # Content
    markdown_content: str = ""  # Extracted text from page

    # Search relevance
    relevance_score: float = 0.0  # Search score (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for API response"""
        pass

@dataclass
class ResearchContext:
    """Formatted context for LLM prompt"""
    formatted_text: str  # Context string with citations
    sources: List[SourceDocument]  # Source documents in citation order
    total_tokens: int  # Approximate token count
    truncated: bool  # Whether context was truncated to fit budget

    def get_citation_map(self) -> Dict[int, SourceDocument]:
        """
        Map citation numbers to source documents

        Returns:
            Dict mapping citation IDs (1, 2, 3...) to SourceDocument

        Example:
            >>> context.get_citation_map()
            {1: SourceDocument(filename="doc1.pdf", page=3), ...}
        """
        pass
```

### Class: `ContextBuilder`

```python
from src.search.search_engine import SearchEngine
from src.storage.chroma_client import ChromaClient

class ContextBuilder:
    """Builds formatted context from search results"""

    def __init__(
        self,
        search_engine: SearchEngine,
        chroma_client: ChromaClient,
        max_sources: int = 10,
        max_tokens: int = 10000
    ):
        """
        Initialize context builder

        Args:
            search_engine: Configured search engine instance
            chroma_client: ChromaDB client for metadata retrieval
            max_sources: Maximum number of sources to include (default: 10)
            max_tokens: Maximum context tokens (default: 10K for ~8K context)

        Note:
            max_tokens includes overhead for formatting, aim for ~80% of model's limit
        """
        pass

    async def build_context(
        self,
        query: str,
        num_results: int = 10,
        include_text: bool = True,
        include_visual: bool = True
    ) -> ResearchContext:
        """
        Build research context from search results

        Args:
            query: User's research question
            num_results: Number of search results to retrieve (default: 10)
            include_text: Include text collection results (default: True)
            include_visual: Include visual collection results (default: True)

        Returns:
            ResearchContext with formatted text and source documents

        Process:
            1. Execute semantic search via SearchEngine
            2. Deduplicate by (doc_id, page) keeping highest scores
            3. Retrieve full markdown via ChromaClient.get_document_markdown()
            4. Format as numbered citations [1], [2], etc.
            5. Truncate if exceeds max_tokens

        Example:
            >>> context = await builder.build_context("What caused the crisis?")
            >>> print(context.formatted_text)
            [Document 1: crisis.pdf, Page 3]
            The financial crisis of 2008 was caused by...

            [Document 2: economics.pdf, Page 12]
            Subprime mortgages played a key role...

            >>> print(len(context.sources))  # 10
            >>> print(context.total_tokens)  # 8500
        """
        pass

    async def get_source_metadata(
        self,
        doc_id: str,
        page: int
    ) -> SourceDocument:
        """
        Retrieve metadata for a single source document

        Args:
            doc_id: Document identifier
            page: Page number

        Returns:
            SourceDocument with all available metadata

        Raises:
            ValueError: If document not found in ChromaDB

        Example:
            >>> source = await builder.get_source_metadata("abc123", 5)
            >>> print(source.filename)  # "report.pdf"
            >>> print(source.thumbnail_path)  # "/data/images/abc123_page_005_thumb.jpg"
        """
        pass

    def format_source_citation(
        self,
        source: SourceDocument,
        citation_num: int
    ) -> str:
        """
        Format a single source as citation block

        Args:
            source: Source document to format
            citation_num: Citation number (1, 2, 3...)

        Returns:
            Formatted citation string

        Example:
            >>> citation = builder.format_source_citation(source, 1)
            >>> print(citation)
            [Document 1: crisis.pdf, Page 3]
            The financial crisis of 2008 was caused by subprime mortgages...
        """
        pass

    def deduplicate_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate (doc_id, page) pairs, keeping highest scores

        Args:
            results: Search results from SearchEngine

        Returns:
            Deduplicated results sorted by score descending

        Example:
            >>> results = [
            ...     {"doc_id": "abc", "page": 1, "score": 0.95},
            ...     {"doc_id": "abc", "page": 1, "score": 0.90},  # Duplicate
            ...     {"doc_id": "def", "page": 2, "score": 0.85}
            ... ]
            >>> deduped = builder.deduplicate_results(results)
            >>> len(deduped)  # 2 (duplicate removed)
        """
        pass

    def truncate_to_budget(
        self,
        sources: List[SourceDocument],
        max_tokens: int
    ) -> List[SourceDocument]:
        """
        Truncate sources to fit token budget

        Args:
            sources: Source documents sorted by relevance
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated list of sources that fit within budget

        Process:
            1. Estimate tokens for each source (citation header + content)
            2. Add sources in order until budget exceeded
            3. Return sources that fit

        Example:
            >>> sources = [source1, source2, source3, ...]  # 15K tokens total
            >>> truncated = builder.truncate_to_budget(sources, max_tokens=10000)
            >>> len(truncated)  # 7 sources (9800 tokens)
        """
        pass

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        Args:
            text: Text to estimate

        Returns:
            Approximate token count

        Note:
            Uses simple heuristic: ~4 chars per token
            More accurate than char count, faster than tiktoken
        """
        pass
```

---

## Data Flow

### Input: User Query
```python
query = "What caused the 2008 financial crisis?"
```

### Step 1: Search Execution
```python
# Context builder calls SearchEngine
search_results = await search_engine.search(
    query=query,
    num_results=10,
    search_mode="hybrid"  # Both visual and text
)

# Example results:
[
    {
        "doc_id": "abc123",
        "page": 3,
        "score": 0.95,
        "filename": "crisis-report.pdf",
        "metadata": {...}
    },
    {
        "doc_id": "abc123",
        "page": 4,
        "score": 0.92,
        "filename": "crisis-report.pdf",
        "metadata": {...}
    },
    {
        "doc_id": "def456",
        "page": 12,
        "score": 0.88,
        "filename": "economics.pdf",
        "metadata": {...}
    },
    ...
]
```

### Step 2: Deduplication
```python
# Remove duplicates by (doc_id, page), keeping highest scores
deduped_results = [
    {"doc_id": "abc123", "page": 3, "score": 0.95},  # Kept
    {"doc_id": "abc123", "page": 4, "score": 0.92},  # Kept (different page)
    {"doc_id": "def456", "page": 12, "score": 0.88},
    ...
]
```

### Step 3: Metadata Retrieval
```python
# For each result, get full metadata and markdown
sources = []
for result in deduped_results[:max_sources]:
    # Get compressed markdown from ChromaDB
    markdown = await chroma_client.get_document_markdown(result["doc_id"])

    # Extract page-specific content
    page_content = extract_page_content(markdown, result["page"])

    # Build SourceDocument
    source = SourceDocument(
        doc_id=result["doc_id"],
        filename=result["filename"],
        page=result["page"],
        extension=result["metadata"]["extension"],
        thumbnail_path=result["metadata"]["thumb_path"],
        timestamp=result["metadata"]["timestamp"],
        section_path=result["metadata"].get("section_path"),
        parent_heading=result["metadata"].get("parent_heading"),
        markdown_content=page_content,
        relevance_score=result["score"]
    )
    sources.append(source)
```

### Step 4: Context Formatting
```python
# Format as numbered citations
formatted_parts = []
for i, source in enumerate(sources, start=1):
    citation = f"[Document {i}: {source.filename}, Page {source.page}]\n"
    citation += source.markdown_content
    formatted_parts.append(citation)

formatted_text = "\n\n".join(formatted_parts)
```

### Step 5: Token Budget Management
```python
# Estimate tokens
total_tokens = estimate_tokens(formatted_text)

# Truncate if necessary
if total_tokens > max_tokens:
    sources = truncate_to_budget(sources, max_tokens)
    # Reformat with truncated sources
    formatted_text = format_truncated_context(sources)
    truncated = True
else:
    truncated = False
```

### Output: ResearchContext
```python
context = ResearchContext(
    formatted_text="""
[Document 1: crisis-report.pdf, Page 3]
The 2008 financial crisis was caused by a combination of factors including
subprime mortgages, excessive leverage, and regulatory failures...

[Document 2: crisis-report.pdf, Page 4]
The collapse of Lehman Brothers in September 2008 triggered a global
financial panic...

[Document 3: economics.pdf, Page 12]
Subprime mortgages played a key role. Banks issued loans to borrowers
with poor credit histories...
""",
    sources=[source1, source2, source3, ...],
    total_tokens=8500,
    truncated=False
)
```

---

## ChromaDB Integration

### Metadata Extraction

```python
# From existing ChromaClient
async def get_source_metadata(self, doc_id: str, page: int) -> SourceDocument:
    # Query visual collection for page metadata
    visual_results = self.chroma_client.visual_collection.get(
        where={
            "$and": [
                {"doc_id": {"$eq": doc_id}},
                {"page": {"$eq": page}}
            ]
        },
        include=["metadatas"]
    )

    if not visual_results["ids"]:
        raise ValueError(f"Document {doc_id} page {page} not found")

    metadata = visual_results["metadatas"][0]

    # Get full markdown (compressed in metadata)
    markdown = await self.chroma_client.get_document_markdown(doc_id)

    # Extract page-specific content
    page_content = self._extract_page_from_markdown(markdown, page)

    return SourceDocument(
        doc_id=doc_id,
        filename=metadata["filename"],
        page=page,
        extension=metadata["extension"],
        thumbnail_path=metadata.get("thumb_path"),
        image_path=metadata.get("image_path"),
        timestamp=metadata["timestamp"],
        section_path=metadata.get("section_path"),
        parent_heading=metadata.get("parent_heading"),
        markdown_content=page_content,
        relevance_score=0.0  # Set by search
    )
```

### Available Metadata Fields

From `src/storage/metadata_schema.py`:

- **Core:** `doc_id`, `filename`, `page`, `extension`, `timestamp`
- **Paths:** `source_path`, `image_path`, `thumb_path`
- **Structure:** `section_path`, `parent_heading`, `num_headings`, `num_tables`, `num_pictures`
- **Content:** `full_markdown_compressed` (gzip + base64)

---

## Usage Examples

### Basic Context Building

```python
from src.research.context_builder import ContextBuilder
from src.search.search_engine import SearchEngine
from src.storage.chroma_client import ChromaClient

# Initialize dependencies
search_engine = SearchEngine(...)
chroma_client = ChromaClient(...)

# Create context builder
builder = ContextBuilder(
    search_engine=search_engine,
    chroma_client=chroma_client,
    max_sources=10,
    max_tokens=10000
)

# Build context for research query
context = await builder.build_context(
    query="What are the benefits of renewable energy?",
    num_results=10
)

print(context.formatted_text)
# [Document 1: renewable-energy.pdf, Page 5]
# Renewable energy sources like solar and wind...
#
# [Document 2: climate-report.pdf, Page 12]
# The environmental benefits include reduced CO2 emissions...

print(f"Sources: {len(context.sources)}")  # 10
print(f"Tokens: {context.total_tokens}")  # 8500
print(f"Truncated: {context.truncated}")  # False
```

### Visual-Only Search

```python
# Search only visual collection (for image-heavy documents)
context = await builder.build_context(
    query="Show me charts about stock market trends",
    num_results=5,
    include_text=False,  # Visual only
    include_visual=True
)

# Sources will be pages with relevant charts/graphs
```

### Token Budget Management

```python
# Strict token budget for cheaper models
small_builder = ContextBuilder(
    search_engine=search_engine,
    chroma_client=chroma_client,
    max_sources=5,  # Fewer sources
    max_tokens=3000  # GPT-3.5's smaller context
)

context = await small_builder.build_context(query="Brief overview of AI?")
print(context.truncated)  # Likely True if query is broad
```

### Citation Mapping

```python
context = await builder.build_context(query="...")

# Get citation map for frontend
citation_map = context.get_citation_map()
# {
#     1: SourceDocument(filename="doc1.pdf", page=3, ...),
#     2: SourceDocument(filename="doc2.pdf", page=5, ...),
#     ...
# }

# Use for reference cards in frontend
for citation_num, source in citation_map.items():
    print(f"[{citation_num}] {source.filename} - Page {source.page}")
```

---

## Integration Points

### Consumed By: Research API (Agent 4)

```python
# src/api/research.py
from src.research.context_builder import ContextBuilder, ResearchContext

@app.post("/api/research/ask")
async def ask_research_question(request: ResearchRequest):
    # Build context
    context: ResearchContext = await app.state.context_builder.build_context(
        query=request.query,
        num_results=10
    )

    # Pass to LLM client
    llm_response = await app.state.llm_client.complete_with_context(
        query=request.query,
        context=context.formatted_text,
        system_message=RESEARCH_SYSTEM_PROMPT
    )

    # Return answer with sources
    return {
        "answer": llm_response.content,
        "sources": [source.to_dict() for source in context.sources],
        "truncated": context.truncated,
        "total_tokens": context.total_tokens
    }
```

### Depends On: Search Engine (Existing)

```python
# src/search/search_engine.py
class SearchEngine:
    async def search(
        self,
        query: str,
        num_results: int = 10,
        search_mode: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Returns list of search results with metadata

        Each result:
        {
            "doc_id": str,
            "page": int,
            "score": float,
            "filename": str,
            "metadata": {...}
        }
        """
```

### Depends On: ChromaDB Client (Existing)

```python
# src/storage/chroma_client.py
class ChromaClient:
    async def get_document_markdown(self, doc_id: str) -> Optional[str]:
        """Retrieve and decompress full markdown text"""

    def visual_collection.get(
        where: Dict,
        include: List[str]
    ) -> Dict:
        """Query visual collection for metadata"""
```

---

## Testing Requirements

### Unit Tests

1. **Context Building**
   - Valid query returns ResearchContext
   - Sources list matches num_results (or less if fewer found)
   - Formatted text includes all sources in order
   - Citation numbers are sequential [1], [2], [3]...

2. **Deduplication**
   - Duplicate (doc_id, page) pairs removed
   - Highest score variant kept
   - Order preserved by score descending

3. **Token Management**
   - estimate_tokens() within 10% of actual
   - truncate_to_budget() respects max_tokens
   - Truncation removes lowest-scored sources first

4. **Metadata Retrieval**
   - get_source_metadata() returns complete SourceDocument
   - Missing documents raise ValueError
   - Markdown extraction works for multi-page docs

### Integration Tests

1. **End-to-End Context Building**
   - Real query → search → context
   - All sources have valid metadata
   - Markdown content extracted correctly

2. **ChromaDB Integration**
   - Metadata retrieved from visual collection
   - Compressed markdown decompressed successfully
   - Page-specific content extracted

3. **Search Integration**
   - Hybrid mode returns both visual and text results
   - Deduplication works across collections
   - Scores sorted correctly

---

## Performance Requirements

- **Context Building:** <1s for 10 sources
- **Metadata Retrieval:** <100ms per source (parallelized)
- **Deduplication:** <10ms for 100 results
- **Token Estimation:** <5ms for 10K characters

---

## Dependencies

```python
# requirements.txt (already in project)
# Search engine and ChromaDB client are existing components
```

---

## Validation Gates (Wave 1)

- [ ] All unit tests pass
- [ ] Integration test with real ChromaDB succeeds
- [ ] Context formatted correctly with citations
- [ ] Deduplication removes duplicates properly
- [ ] Token budget respected (no overruns)
- [ ] Metadata extraction includes all fields
- [ ] Page-specific content extracted accurately
- [ ] Performance requirements met

---

## Notes

- Reuses existing SearchEngine (2-stage search validated in Wave 3+4)
- Leverages existing ChromaDB metadata infrastructure
- Page-specific markdown extraction needed (not currently exposed)
- Token estimation uses heuristic (~4 chars/token) for speed
- Max 10 sources balances context richness vs token budget
- Deduplication essential for hybrid search (same page in both collections)
