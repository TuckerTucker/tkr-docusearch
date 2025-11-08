"""
Core types module for DocuSearch.

This module provides shared type definitions, TypedDicts, and type aliases used
across the DocuSearch application. Following Inversion of Control (IoC) principles,
all shared types should be defined here to avoid circular dependencies.

Future Type Categories:
    - Document types (metadata, chunks, pages)
    - Search types (queries, results, embeddings)
    - Research types (sources, citations, responses)
    - Storage types (collection metadata, index info)
    - Processing types (task status, progress tracking)

Design Principles:
    - Use TypedDict for structured dictionaries (Python 3.8+)
    - Use dataclasses for more complex types with methods
    - Provide clear docstrings with examples
    - Support both strict and gradual typing
    - Enable mypy type checking

Usage:
    >>> from src.core.types import DocumentMetadata
    >>> metadata: DocumentMetadata = {
    ...     "doc_id": "abc123",
    ...     "filename": "document.pdf",
    ...     "doc_type": "visual"
    ... }

Note:
    This module is currently a placeholder for future centralized type definitions.
    As part of Quality Improvement Sprint Wave 2, types will be migrated here
    from individual modules.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

# =============================================================================
# Document Types (Placeholders for Wave 2 migration)
# =============================================================================

# Example type definitions that will be added during migration:
#
# class DocumentMetadata(TypedDict, total=False):
#     """Document metadata structure."""
#     doc_id: str
#     filename: str
#     doc_type: Literal["visual", "text", "audio"]
#     page_count: Optional[int]
#     chunk_count: Optional[int]
#     upload_date: str
#     file_size: int
#     mime_type: str
#
# class ChunkMetadata(TypedDict):
#     """Chunk metadata structure."""
#     chunk_id: str
#     doc_id: str
#     chunk_index: int
#     page_number: Optional[int]
#     timestamp: Optional[float]
#     text: Optional[str]
#     image_path: Optional[str]
#
# class SearchResult(TypedDict):
#     """Search result structure."""
#     doc_id: str
#     chunk_id: str
#     score: float
#     metadata: ChunkMetadata
#     snippet: Optional[str]


# =============================================================================
# Type Aliases (Placeholders for Wave 2 migration)
# =============================================================================

# Common type aliases
DocID = str
ChunkID = str
EmbeddingVector = List[float]
Score = float

# Document type literals
DocType = Literal["visual", "text", "audio"]
ProcessingStatus = Literal["pending", "processing", "complete", "failed"]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Type aliases
    "DocID",
    "ChunkID",
    "EmbeddingVector",
    "Score",
    "DocType",
    "ProcessingStatus",
    # TypedDict classes will be added during Wave 2 migration
]
