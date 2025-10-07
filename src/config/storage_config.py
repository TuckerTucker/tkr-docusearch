"""
Storage configuration for ChromaDB.

This module defines configuration for ChromaDB connection and collections.
"""

from dataclasses import dataclass
import os


@dataclass
class StorageConfig:
    """ChromaDB storage configuration.

    Attributes:
        host: ChromaDB server host
        port: ChromaDB server port
        visual_collection: Name of visual embeddings collection
        text_collection: Name of text embeddings collection
        batch_size: Batch size for ChromaDB operations
        persist_directory: Directory for ChromaDB persistence
    """

    # Connection
    host: str = os.getenv('CHROMA_HOST', 'chromadb')
    port: int = int(os.getenv('CHROMA_PORT', '8001'))

    # Collections
    visual_collection: str = os.getenv('VISUAL_COLLECTION', 'visual_collection')
    text_collection: str = os.getenv('TEXT_COLLECTION', 'text_collection')

    # Batch operations
    batch_size: int = int(os.getenv('CHROMA_BATCH_SIZE', '100'))

    # Persistence
    persist_directory: str = os.getenv('CHROMA_DATA', '/chroma/chroma')

    @property
    def connection_string(self) -> str:
        """Get ChromaDB connection string.

        Returns:
            HTTP connection string
        """
        return f"http://{self.host}:{self.port}"

    @property
    def connection_url(self) -> str:
        """Alias for connection_string for compatibility.

        Returns:
            HTTP connection string
        """
        return self.connection_string

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            'host': self.host,
            'port': self.port,
            'connection_string': self.connection_string,
            'visual_collection': self.visual_collection,
            'text_collection': self.text_collection,
            'batch_size': self.batch_size,
            'persist_directory': self.persist_directory,
        }

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"StorageConfig("
            f"connection='{self.connection_string}', "
            f"visual='{self.visual_collection}', "
            f"text='{self.text_collection}')"
        )
