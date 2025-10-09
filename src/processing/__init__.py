"""
Document processing pipeline.

This module provides the complete document processing pipeline including:
- Document parsing (Docling)
- Visual embedding generation
- Text embedding generation
- Storage coordination

For Wave 2, this uses mock implementations of embedding and storage agents.
Wave 3 will integrate real implementations.
"""

from .processor import (
    DocumentProcessor,
    ProcessingStatus,
    StorageConfirmation,
    ProcessingError,
    EmbeddingError,
    StorageError
)
from .docling_parser import (
    DoclingParser,
    ParsedDocument,
    Page,
    TextChunk,
    ParsingError
)
from .visual_processor import (
    VisualProcessor,
    VisualEmbeddingResult
)
from .text_processor import (
    TextProcessor,
    TextEmbeddingResult
)
from .mocks import (
    MockEmbeddingEngine,
    MockStorageClient,
    BatchEmbeddingOutput
)
from .preview_generator import (
    PreviewGenerator,
    PreviewResponse
)

__all__ = [
    # Main processor
    "DocumentProcessor",
    "ProcessingStatus",
    "StorageConfirmation",
    "ProcessingError",
    "EmbeddingError",
    "StorageError",
    # Parser
    "DoclingParser",
    "ParsedDocument",
    "Page",
    "TextChunk",
    "ParsingError",
    # Visual processing
    "VisualProcessor",
    "VisualEmbeddingResult",
    # Text processing
    "TextProcessor",
    "TextEmbeddingResult",
    # Mocks (Wave 2)
    "MockEmbeddingEngine",
    "MockStorageClient",
    "BatchEmbeddingOutput",
    # Preview generation (Wave 2, Agent 3)
    "PreviewGenerator",
    "PreviewResponse",
]
