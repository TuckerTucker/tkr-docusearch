"""Document processing pipeline.

Delegates parsing, chunking, and text embedding to ``shikomi.Ingester``.
Page rendering, visual embedding, and Koji storage are coordinated by
``DocumentProcessor``.
"""

from .processor import (
    DocumentProcessor,
    EmbeddingError,
    ProcessingError,
    ProcessingStatus,
    StorageConfirmation,
    StorageError,
)
from .shikomi_ingester import ShikomiIngester

__all__ = [
    # Main processor
    "DocumentProcessor",
    "ProcessingStatus",
    "StorageConfirmation",
    "ProcessingError",
    "EmbeddingError",
    "StorageError",
    # Ingester
    "ShikomiIngester",
]
