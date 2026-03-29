"""
Storage handlers for embedding operations.

This module contains handler classes for metadata filtering and album art
extraction, reducing complexity in DocumentProcessor.
"""

from .album_art_handler import AlbumArtHandler
from .metadata_filter import MetadataFilter

__all__ = [
    "MetadataFilter",
    "AlbumArtHandler",
]
