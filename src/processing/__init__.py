"""
Document processing pipeline.

This module provides the complete document processing pipeline including:
- Document parsing (Docling)
- Visual embedding generation (Shikomi)
- Text embedding generation (Shikomi)
- Storage coordination (Koji)
"""

from .docling_parser import DoclingParser, Page, ParsedDocument, ParsingError, TextChunk
from .preview_generator import PreviewGenerator, PreviewResponse
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
    # Preview generation
    "PreviewGenerator",
    "PreviewResponse",
]
