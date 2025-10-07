# Smart Chunking Contract

**Contract ID**: CHUNK-001
**Version**: 1.0
**Status**: Specification
**Owner**: chunking-agent
**Consumers**: metadata-agent, integration-agent

## Purpose

Define the interface and data format for document-aware smart chunking using Docling's HybridChunker, including chunk context metadata and integration with the legacy chunking system.

## Data Structures

### ChunkContext

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ChunkContext:
    """Contextual metadata for a text chunk."""

    # Parent heading (if chunk is under a heading)
    parent_heading: Optional[str] = None
    parent_heading_level: Optional[int] = None  # 0=title, 1=section, 2=subsection

    # Section path (breadcrumb of headings)
    section_path: str = ""  # e.g., "Introduction > Methods > Data Collection"

    # Element type
    element_type: str = "text"  # text, list_item, table_cell, caption, code, formula

    # Related elements (tables/figures mentioned in chunk)
    related_tables: List[str] = None  # table IDs
    related_pictures: List[str] = None  # picture IDs

    # Position information
    page_nums: List[int] = None  # Pages spanned by chunk (usually 1, rarely 2+)
    is_page_boundary: bool = False  # True if chunk crosses page boundary

    def __post_init__(self):
        """Initialize default values."""
        if self.related_tables is None:
            self.related_tables = []
        if self.related_pictures is None:
            self.related_pictures = []
        if self.page_nums is None:
            self.page_nums = []

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "parent_heading": self.parent_heading,
            "parent_heading_level": self.parent_heading_level,
            "section_path": self.section_path,
            "element_type": self.element_type,
            "related_tables": self.related_tables,
            "related_pictures": self.related_pictures,
            "page_nums": self.page_nums,
            "is_page_boundary": self.is_page_boundary
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChunkContext":
        """Create from dictionary."""
        return cls(**data)
```

### Enhanced TextChunk

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TextChunk:
    """Enhanced text chunk with context metadata.

    Backward compatible with existing TextChunk structure,
    with additional context field.
    """
    chunk_id: str
    page_num: int  # Primary page (for backward compat)
    text: str
    start_offset: int
    end_offset: int
    word_count: int

    # New field for enhanced mode
    context: Optional[ChunkContext] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        data = {
            "chunk_id": self.chunk_id,
            "page_num": self.page_num,
            "text": self.text,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "word_count": self.word_count
        }
        if self.context:
            data["context"] = self.context.to_dict()
        return data
```

## Chunking Interface

### Main SmartChunker Class

```python
from typing import List, Iterator
from docling.chunking import HybridChunker
from docling_core.types.doc import DoclingDocument
from transformers import AutoTokenizer

class SmartChunker:
    """Document-aware chunker using Docling's HybridChunker."""

    def __init__(self, config: EnhancedModeConfig):
        """
        Initialize smart chunker.

        Args:
            config: Enhanced mode configuration
        """
        self.config = config

        # Initialize tokenizer (match text embedding model)
        self.tokenizer = self._init_tokenizer()

        # Initialize HybridChunker
        self.hybrid_chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=config.max_chunk_tokens,
            min_chunk_tokens=config.min_chunk_tokens,
            merge_peers=config.merge_peer_chunks
        )

    def _init_tokenizer(self):
        """Initialize tokenizer matching embedding model."""
        # TODO: Detect from embedding engine or config
        # For now, use common default
        model_name = "bert-base-uncased"  # Match your text embedding model
        return AutoTokenizer.from_pretrained(model_name)

    def chunk_document(
        self,
        doc: DoclingDocument,
        doc_id: str,
        structure: DocumentStructure
    ) -> List[TextChunk]:
        """
        Chunk document using hybrid strategy.

        Args:
            doc: Parsed DoclingDocument
            doc_id: Document identifier
            structure: Extracted document structure

        Returns:
            List of TextChunk with context metadata
        """
        chunks = []

        # Use HybridChunker to get base chunks
        for idx, base_chunk in enumerate(self.hybrid_chunker.chunk(doc)):
            # Extract context from base chunk metadata
            context = self._extract_chunk_context(base_chunk, structure)

            # Determine primary page
            page_num = context.page_nums[0] if context.page_nums else 1

            # Create enhanced TextChunk
            chunk = TextChunk(
                chunk_id=f"{doc_id}-chunk{idx:04d}",
                page_num=page_num,
                text=base_chunk.text,
                start_offset=0,  # HybridChunker doesn't provide char offsets
                end_offset=len(base_chunk.text),
                word_count=len(base_chunk.text.split()),
                context=context
            )
            chunks.append(chunk)

        return chunks

    def _extract_chunk_context(
        self,
        base_chunk,
        structure: DocumentStructure
    ) -> ChunkContext:
        """Extract contextual metadata from HybridChunker output."""
        context = ChunkContext()

        # Extract from base_chunk.meta (provided by HybridChunker)
        meta = base_chunk.meta

        # Get parent heading
        if hasattr(meta, 'headings') and meta.headings:
            # HybridChunker provides list of parent headings
            context.parent_heading = meta.headings[-1]  # Immediate parent
            context.section_path = " > ".join(meta.headings)

            # Look up heading level from structure
            for heading_info in structure.headings:
                if heading_info.text == context.parent_heading:
                    context.parent_heading_level = heading_info.level.value
                    break

        # Get element type
        if hasattr(meta, 'doc_items') and meta.doc_items:
            # Determine type from first doc item
            first_item = meta.doc_items[0]
            if hasattr(first_item, 'label'):
                context.element_type = self._map_element_type(first_item.label)

        # Get page numbers
        if hasattr(meta, 'doc_items'):
            page_nums_set = set()
            for item in meta.doc_items:
                if hasattr(item, 'prov') and item.prov:
                    page_nums_set.add(item.prov[0].page_no)
            context.page_nums = sorted(list(page_nums_set))
            context.is_page_boundary = len(context.page_nums) > 1

        # Detect related tables/pictures (if chunk mentions them)
        context.related_tables = self._find_related_elements(
            base_chunk.text, structure.tables, "Table"
        )
        context.related_pictures = self._find_related_elements(
            base_chunk.text, structure.pictures, "Figure"
        )

        return context

    def _map_element_type(self, docling_label: str) -> str:
        """Map Docling label to element type."""
        mapping = {
            "TEXT": "text",
            "LIST_ITEM": "list_item",
            "TABLE": "table_cell",
            "CAPTION": "caption",
            "CODE": "code",
            "FORMULA": "formula"
        }
        return mapping.get(docling_label, "text")

    def _find_related_elements(
        self,
        text: str,
        elements: List,
        prefix: str
    ) -> List[str]:
        """Find references to tables/figures in chunk text."""
        import re
        related = []
        # Look for "Table 1", "Figure 2", etc.
        pattern = rf"{prefix}\s+(\d+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            element_id = f"{prefix.lower()}-{int(match) - 1}"  # 0-indexed
            related.append(element_id)
        return related
```

### Legacy Chunker Wrapper

```python
class LegacyChunker:
    """Backward-compatible word-based chunker."""

    def __init__(self, chunk_size_words: int = 250, chunk_overlap_words: int = 50):
        """Initialize legacy chunker with word-based parameters."""
        self.chunk_size_words = chunk_size_words
        self.chunk_overlap_words = chunk_overlap_words

    def chunk_pages(
        self,
        pages: List[Page],
        doc_id: str
    ) -> List[TextChunk]:
        """
        Chunk pages using word-based sliding window.

        This is the existing implementation from docling_parser.py,
        wrapped for consistency with SmartChunker interface.
        """
        # Existing _chunk_text() logic
        # Returns TextChunk objects without context field
        pass
```

### Chunking Strategy Router

```python
def create_chunker(config: EnhancedModeConfig):
    """Create appropriate chunker based on configuration."""
    if config.chunking_strategy == ChunkingStrategy.HYBRID:
        return SmartChunker(config)
    else:
        return LegacyChunker(
            chunk_size_words=250,
            chunk_overlap_words=50
        )
```

## Integration with Docling Parser

### Updated _chunk_text Method

```python
# In DoclingParser class

def _chunk_document(
    self,
    doc: DoclingDocument,
    pages: List[Page],
    doc_id: str,
    structure: DocumentStructure,
    config: EnhancedModeConfig
) -> List[TextChunk]:
    """
    Chunk document using configured strategy.

    Args:
        doc: DoclingDocument (for hybrid chunking)
        pages: List of Page objects (for legacy chunking)
        doc_id: Document identifier
        structure: Extracted structure
        config: Enhanced mode configuration

    Returns:
        List of TextChunk objects
    """
    chunker = create_chunker(config)

    if isinstance(chunker, SmartChunker):
        # Use document-aware chunking
        return chunker.chunk_document(doc, doc_id, structure)
    else:
        # Use legacy page-based chunking
        return chunker.chunk_pages(pages, doc_id)
```

## Contextualized Text for Embedding

### Context Enrichment

```python
def contextualize_chunk(chunk: TextChunk) -> str:
    """
    Create context-enriched text for embedding.

    Prepends structural context to chunk text to improve embedding quality.

    Args:
        chunk: TextChunk with context metadata

    Returns:
        Contextualized text string
    """
    if not chunk.context:
        return chunk.text

    parts = []

    # Add section path
    if chunk.context.section_path:
        parts.append(f"[Section: {chunk.context.section_path}]")

    # Add element type if not plain text
    if chunk.context.element_type != "text":
        parts.append(f"[Type: {chunk.context.element_type}]")

    # Add related elements
    if chunk.context.related_tables:
        parts.append(f"[Refers to: {', '.join(chunk.context.related_tables)}]")
    if chunk.context.related_pictures:
        parts.append(f"[Refers to: {', '.join(chunk.context.related_pictures)}]")

    # Add original text
    parts.append(chunk.text)

    return " ".join(parts)
```

**Note**: Contextualization is optional. You can:
1. Embed raw chunk text (simpler, smaller)
2. Embed contextualized text (richer semantics, larger)
3. Store context in metadata only (query-time usage)

## Performance Requirements

- **Chunking time**: <10% of total processing time
- **Chunk quality**: Measurably better boundaries than word-based
- **Context overhead**: <2KB per chunk in metadata
- **Tokenization**: Cached for efficiency

## Validation Requirements

### Chunk Validation

```python
def validate_chunk(chunk: TextChunk) -> None:
    """Validate chunk structure and content."""
    # Basic validation
    assert chunk.text.strip(), "Empty chunk text"
    assert chunk.word_count > 0, "Invalid word count"
    assert chunk.chunk_id, "Missing chunk ID"

    # Context validation (if present)
    if chunk.context:
        assert chunk.page_num in chunk.context.page_nums or not chunk.context.page_nums, \
            "Primary page not in context pages"

        if chunk.context.section_path:
            assert len(chunk.context.section_path) < 500, "Section path too long"
```

## Testing Contract

### Unit Tests Required
- ✅ SmartChunker initializes correctly
- ✅ Chunks extracted from sample document
- ✅ Context metadata populated accurately
- ✅ Legacy chunker still works
- ✅ Chunking strategy router works
- ✅ Contextualize function formats correctly

### Integration Tests Required
- ✅ Hybrid chunking produces quality chunks
- ✅ Chunk boundaries respect document structure
- ✅ Context enrichment improves search quality
- ✅ Performance within targets

## Backward Compatibility

### Handling Legacy Documents

Chunks without context should work seamlessly:
```python
# Old chunk (no context)
chunk_old = TextChunk(
    chunk_id="doc-1-chunk0001",
    page_num=1,
    text="This is some text.",
    start_offset=0,
    end_offset=18,
    word_count=4
)

# New chunk (with context)
chunk_new = TextChunk(
    chunk_id="doc-2-chunk0001",
    page_num=1,
    text="This is some text.",
    start_offset=0,
    end_offset=18,
    word_count=4,
    context=ChunkContext(parent_heading="Introduction")
)

# Both work in storage and search
```

## File Locations

- `src/processing/smart_chunker.py` - Smart chunker implementation
- `src/processing/docling_parser.py` - Integration point

## Version History

- **1.0** (2025-10-07): Initial specification
