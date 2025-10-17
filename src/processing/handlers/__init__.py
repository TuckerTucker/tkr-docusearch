"""
Storage handlers for embedding operations.

This module contains handler classes for storing visual and text embeddings,
reducing complexity in DocumentProcessor.
"""

from .album_art_handler import AlbumArtHandler
from .metadata_filter import MetadataFilter
from .text_embedding_handler import TextEmbeddingHandler
from .visual_embedding_handler import VisualEmbeddingHandler

__all__ = [
    "VisualEmbeddingHandler",
    "TextEmbeddingHandler",
    "MetadataFilter",
    "AlbumArtHandler",
]
