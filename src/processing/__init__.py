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

from .docling_parser import DoclingParser, Page, ParsedDocument, ParsingError, TextChunk
from .mocks import BatchEmbeddingOutput, MockEmbeddingEngine, MockStorageClient
from .processor import (
    DocumentProcessor,
    EmbeddingError,
    ProcessingError,
    ProcessingStatus,
    StorageConfirmation,
    StorageError,
)
from .text_processor import TextEmbeddingResult, TextProcessor
from .visual_processor import VisualEmbeddingResult, VisualProcessor

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
]
